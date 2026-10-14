from pathlib import Path
import requests
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import msal
from msal_extensions import (
    PersistedTokenCache,
    FilePersistenceWithDataProtection,
)
from app.config import GRAPH_CONFIG


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "output"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "msal_graph_cache.bin"


class GraphClient:
    def __init__(self):
        self.tenant_id = GRAPH_CONFIG["tenant_id"]
        self.client_id = GRAPH_CONFIG["client_id"]
        self.site_id = GRAPH_CONFIG["site_id"]
        self.site_url = GRAPH_CONFIG.get("site_url")
        self.list_ids = GRAPH_CONFIG["list_ids"]
        self.scopes = GRAPH_CONFIG["scopes"]
        self.token = None
        self.logger = logging.getLogger(__name__)

        self.cache = self._build_token_cache()
        self.app = self._build_public_client_app()
        self.session = requests.Session()

    def _build_token_cache(self):
        persistence = FilePersistenceWithDataProtection(str(CACHE_FILE))
        return PersistedTokenCache(persistence)

    def _build_public_client_app(self):
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"

        return msal.PublicClientApplication(
            client_id=self.client_id,
            authority=authority,
            token_cache=self.cache,
        )

    def is_configured(self) -> bool:
        return all([
            self.tenant_id,
            self.client_id,
            self.site_id,
            self.list_ids,
            self.scopes,
        ])

    def validate_config(self):
        missing = []

        if not self.tenant_id:
            missing.append("GRAPH_TENANT_ID")
        if not self.client_id:
            missing.append("GRAPH_CLIENT_ID")
        if not self.site_id:
            missing.append("GRAPH_SITE_ID")
        if not self.list_ids:
            missing.append("GRAPH_LIST_ID_*")

        if missing:
            raise ValueError(
                "Configuração do Microsoft Graph incompleta. "
                f"Variáveis ausentes no .env: {', '.join(missing)}"
            )

    def get_list_id(self, list_key: str) -> str:
        list_id = self.list_ids.get(list_key)

        if not list_id:
            raise ValueError(
                f"List ID não configurado para '{list_key}'. "
                "Verifique o GRAPH_CONFIG['list_ids'] no config.py e o .env."
            )

        return list_id

    def acquire_token_device_flow(self) -> str:
        flow = self.app.initiate_device_flow(scopes=self.scopes)

        if "user_code" not in flow:
            raise RuntimeError("Não foi possível iniciar o device flow do Microsoft Graph.")

        print(flow["message"])

        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise RuntimeError(
                f"Falha ao obter token do Graph: {result.get('error_description', result)}"
            )

        self.token = result["access_token"]
        self._update_session_headers()
        return self.token

    def acquire_token(self) -> str:
        """
        Tenta primeiro usar cache local.
        Se não conseguir, cai para device code flow.
        """
        self.validate_config()

        accounts = self.app.get_accounts()

        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])

            if result and "access_token" in result:
                self.token = result["access_token"]
                self._update_session_headers()
                return self.token

        return self.acquire_token_device_flow()

    def _update_session_headers(self):
        if not self.token:
            raise RuntimeError("Token do Microsoft Graph ainda não foi obtido.")

        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })

    def get_headers(self) -> dict:
        if not self.token:
            raise RuntimeError("Token do Microsoft Graph ainda não foi obtido.")

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_fields_for_list(self, list_key: str) -> list[str]:
        # Campos de negócio por lista
        if list_key in ("iuh_gerencia", "iuh_supervisao"):
            return [
                "Title",
                "Ano",
                "SemanaISO",
                "DataInicioSemana",
                "DataFimSemana",
                "CR",
                "HorasConfirmadas",
                "HorasCatraca",
                "IUH",
                "Meta",
                "Fonte",
            ]

        if list_key == "hora_extra_gerencia":
            return [
                "Title",
                "Ano",
                "SemanaISO",
                "DataInicioSemana",
                "DataFimSemana",
                "CR",
                "HorasExtras",
                "HorasCatraca",
                "HoraExtraPerc",
                "Meta",
                "Fonte",
            ]

        # Default: no predefined fields (caller will fallback to record keys)
        return []

    def build_list_item_payload(self, record: dict, list_key: str) -> dict:
        # Monta o payload de acordo com os campos esperados para a lista
        fields = {}

        keys = self.get_fields_for_list(list_key)

        # Se não houver mapeamento pré-definido, usa tudo exceto DataAtualizacao
        if not keys:
            keys = [k for k in record.keys() if k != "DataAtualizacao"]

        for k in keys:
            fields[k] = record.get(k)

        # Sempre inclui DataAtualizacao para controle, se presente
        if "DataAtualizacao" in record:
            fields["DataAtualizacao"] = record.get("DataAtualizacao")

        return {"fields": fields}

    def create_list_item(self, record: dict, list_key: str) -> dict:
        self.validate_config()
        list_id = self.get_list_id(list_key)

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{list_id}/items"
        payload = self.build_list_item_payload(record, list_key)

        response = self.session.post(
            url,
            json=payload,
            timeout=30
        )

        if not response.ok:
            raise RuntimeError(
                f"Erro ao criar item na Microsoft List '{list_key}': "
                f"{response.status_code} - {response.text}"
            )

        return response.json()

    def update_list_item(self, item_id: str, record: dict, list_key: str) -> dict:
        self.validate_config()
        list_id = self.get_list_id(list_key)

        url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{list_id}/items/{item_id}/fields"
        payload = self.build_list_item_payload(record, list_key)["fields"]

        response = self.session.patch(
            url,
            json=payload,
            timeout=30
        )

        if not response.ok:
            raise RuntimeError(
                f"Erro ao atualizar item na Microsoft List '{list_key}': "
                f"{response.status_code} - {response.text}"
            )

        if response.content:
            return response.json()
        return {}

    def get_list_items(self, list_key: str) -> list[dict]:
        """
        Retorna TODOS os itens da list, tratando paginação do Graph.
        """
        self.validate_config()
        list_id = self.get_list_id(list_key)

        url = (
            f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{list_id}/items"
            f"?expand=fields"
        )

        items = []

        while url:
            response = self.session.get(url, timeout=30)

            if not response.ok:
                raise RuntimeError(
                    f"Erro ao consultar itens da Microsoft List '{list_key}': "
                    f"{response.status_code} - {response.text}"
                )

            data = response.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")

        return items

    def build_existing_index(self, list_key: str) -> dict[str, dict]:
        """
        Monta índice local com tudo que importa para upsert:
        {
            Title: {
                "id": "...",
                "fields": {...}
            }
        }
        """
        items = self.get_list_items(list_key)
        existing_index = {}

        for item in items:
            item_id = item.get("id")
            fields = item.get("fields", {})
            title = fields.get("Title")

            if title and item_id:
                existing_index[title] = {
                    "id": item_id,
                    "fields": fields
                }

        return existing_index

    def _normalize_value(self, value):
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return round(float(value), 6)

        if isinstance(value, str):
            return value.strip()

        return value

    def has_relevant_changes(self, record: dict, existing_fields: dict, list_key: str) -> bool:
        """
        Compara só os campos de negócio.
        Ignora DataAtualizacao, porque ela muda em toda execução.
        """
        fields_to_compare = self.get_fields_for_list(list_key)

        for field in fields_to_compare:
            new_value = self._normalize_value(record.get(field))
            old_value = self._normalize_value(existing_fields.get(field))

            if new_value != old_value:
                return True

        return False

    def find_item_by_title(
        self,
        title: str,
        list_key: str,
        existing_index: dict[str, dict] | None = None
    ) -> dict | None:
        """
        Mantido por compatibilidade.
        Prefira build_existing_index() e bulk_upsert_list_items().
        """
        if existing_index is None:
            existing_index = self.build_existing_index(list_key)

        existing_item = existing_index.get(title)
        if not existing_item:
            return None

        return existing_item

    def upsert_list_item(
        self,
        record: dict,
        list_key: str,
        existing_index: dict[str, dict] | None = None
    ) -> dict:
        """
        Upsert unitário.
        Retorna status:
        - created
        - updated
        - skipped
        """
        title = record["Title"]

        if existing_index is None:
            existing_index = self.build_existing_index(list_key)

        existing_item = existing_index.get(title)

        if existing_item:
            item_id = existing_item["id"]
            existing_fields = existing_item["fields"]

            if self.has_relevant_changes(record, existing_fields, list_key):
                result = self.update_list_item(item_id, record, list_key)

                existing_index[title] = {
                    "id": item_id,
                    "fields": self.build_list_item_payload(record, list_key)["fields"]
                }

                return {
                    "status": "updated",
                    "id": item_id,
                    "result": result,
                }

            return {
                "status": "skipped",
                "id": item_id,
                "result": None,
            }

        created = self.create_list_item(record, list_key)
        created_id = created.get("id")

        if created_id:
            existing_index[title] = {
                "id": created_id,
                "fields": self.build_list_item_payload(record, list_key)["fields"]
            }

        return {
            "status": "created",
            "id": created_id,
            "result": created,
        }

    def bulk_upsert_list_items(self, records: list[dict], list_key: str) -> dict:
        """
        Otimização:
        - baixa a list UMA vez
        - monta índice Title -> item/fields
        - só atualiza o que mudou
        - cria o que não existe
        - ignora o que já está igual
        - envia em batch (chunks de até 20)
        """
        self.validate_config()

        existing_index = self.build_existing_index(list_key)

        created = 0
        updated = 0
        skipped = 0
        errors = []

        list_id = self.get_list_id(list_key)

        batch_requests = []
        request_map: dict[str, dict] = {}

        for record in records:
            try:
                title = record.get("Title")
                existing_item = existing_index.get(title)

                if existing_item:
                    if self.has_relevant_changes(record, existing_item["fields"], list_key):
                        item_id = existing_item["id"]
                        req_id = str(len(batch_requests))
                        url = f"/sites/{self.site_id}/lists/{list_id}/items/{item_id}/fields"
                        payload = self.build_list_item_payload(record, list_key)["fields"]

                        batch_requests.append({
                            "id": req_id,
                            "method": "PATCH",
                            "url": url,
                            "headers": {"Content-Type": "application/json"},
                            "body": payload,
                        })

                        request_map[req_id] = {
                            "type": "update",
                            "title": title,
                            "record": record,
                            "item_id": item_id,
                        }
                    else:
                        skipped += 1
                else:
                    req_id = str(len(batch_requests))
                    url = f"/sites/{self.site_id}/lists/{list_id}/items"
                    payload = self.build_list_item_payload(record, list_key)

                    batch_requests.append({
                        "id": req_id,
                        "method": "POST",
                        "url": url,
                        "headers": {"Content-Type": "application/json"},
                        "body": payload,
                    })

                    request_map[req_id] = {
                        "type": "create",
                        "title": title,
                        "record": record,
                    }

            except Exception as e:
                errors.append({"Title": record.get("Title"), "error": str(e)})

        def _send_batch(chunk):
            url = "https://graph.microsoft.com/v1.0/$batch"
            headers = self.get_headers()

            t0 = time.perf_counter()
            resp = requests.post(url, headers=headers, json={"requests": chunk}, timeout=60)

            if not resp.ok:
                raise RuntimeError(f"Erro ao enviar batch para o Graph: {resp.status_code} - {resp.text}")

            data = resp.json()
            elapsed = time.perf_counter() - t0
            self.logger.debug("Chunk enviados=%s tempo=%.2fs", len(chunk), elapsed)

            return {r.get("id"): r for r in data.get("responses", [])}

        batch_size = 20
        chunks = [batch_requests[i:i + batch_size] for i in range(0, len(batch_requests), batch_size)]

        if not chunks:
            return {
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
                "total": len(records),
                "success": created + updated + skipped,
            }

        start_time = time.perf_counter()

        max_workers = min(8, len(chunks))
        futures_map = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for chunk in chunks:
                futures_map[executor.submit(_send_batch, chunk)] = chunk

            for future in as_completed(futures_map):
                chunk = futures_map[future]

                try:
                    responses = future.result()
                except Exception as e:
                    for req in chunk:
                        meta = request_map.get(req["id"], {})
                        errors.append({
                            "Title": meta.get("title"),
                            "error": str(e)
                        })
                    continue

                for req in chunk:
                    rid = req["id"]
                    meta = request_map.get(rid, {})
                    title = meta.get("title")

                    resp = responses.get(rid)
                    if not resp:
                        errors.append({
                            "Title": title,
                            "error": "Resposta ausente no batch"
                        })
                        continue

                    status = resp.get("status")
                    body = resp.get("body") or {}

                    if 200 <= status < 300:
                        if meta.get("type") == "create":
                            created += 1
                            created_id = body.get("id")

                            if created_id:
                                existing_index[title] = {
                                    "id": created_id,
                                    "fields": self.build_list_item_payload(meta.get("record"), list_key)["fields"],
                                }
                        else:
                            updated += 1
                            existing_index[title] = {
                                "id": meta.get("item_id"),
                                "fields": self.build_list_item_payload(meta.get("record"), list_key)["fields"],
                            }
                    else:
                        err_text = body.get("error") or body or resp
                        errors.append({
                            "Title": title,
                            "error": str(err_text)
                        })

        elapsed = time.perf_counter() - start_time
        self.logger.info(
            "Batch upload concluído em %.2fs (chunks=%s, workers=%s)",
            elapsed,
            len(chunks),
            max_workers
        )

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(records),
            "success": created + updated + skipped,
        }