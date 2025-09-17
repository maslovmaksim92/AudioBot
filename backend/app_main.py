<file>
<absolute_file_name>/app/backend/app_main.py</absolute_file_name>
<content_replace>
<old>        resp = await bitrix._call("crm.deal.list", {
            "select": [
                "ID", "TITLE", "STAGE_ID", "COMPANY_ID", "COMPANY_TITLE",
                "ASSIGNED_BY_ID", "ASSIGNED_BY_NAME", "CATEGORY_ID",
                "UF_CRM_1669561599956",
                "UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166",
                "UF_CRM_1741592774017","UF_CRM_1741592855565",
                "UF_CRM_1741592892232","UF_CRM_1741592945060",
                "UF_CRM_1741593004888","UF_CRM_1741593047994",
                "UF_CRM_1741593067418","UF_CRM_1741593115407",
                "UF_CRM_1741593156926","UF_CRM_1741593210242",
                "UF_CRM_1741593231558","UF_CRM_1741593285121",
                "UF_CRM_1741593340713","UF_CRM_1741593387667",
                "UF_CRM_1741593408621","UF_CRM_1741593452062"
            ],
            "filter": {"CATEGORY_ID": "34"},
            "order": {"ID": "DESC"},
            "limit": 1000
        })
        raw = resp.get("result") or []</old>
<new>        resp = await bitrix._call("crm.deal.list", {
            "select": [
                "ID", "TITLE", "STAGE_ID", "COMPANY_ID", "COMPANY_TITLE",
                "ASSIGNED_BY_ID", "ASSIGNED_BY_NAME", "CATEGORY_ID",
                "UF_CRM_1669561599956",
                "UF_CRM_1669704529022","UF_CRM_1669705507390","UF_CRM_1669704631166",
                "UF_CRM_1741592774017","UF_CRM_1741592855565",
                "UF_CRM_1741592892232","UF_CRM_1741592945060",
                "UF_CRM_1741593004888","UF_CRM_1741593047994",
                "UF_CRM_1741593067418","UF_CRM_1741593115407",
                "UF_CRM_1741593156926","UF_CRM_1741593210242",
                "UF_CRM_1741593231558","UF_CRM_1741593285121",
                "UF_CRM_1741593340713","UF_CRM_1741593387667",
                "UF_CRM_1741593408621","UF_CRM_1741593452062"
            ],
            "filter": {"CATEGORY_ID": "34"},
            "order": {"ID": "DESC"},
            "limit": 1000
        })
        raw = resp.get("result") or []
        if not resp.get("ok") or raw is None:
            # fallback to cached simplified deals
            basic = await bitrix.deals(limit=1000)
            base_url = bitrix.webhook_url.replace('/rest','') if bitrix.webhook_url else ''
            houses: List[HouseResponse] = []
            for d in basic:
                houses.append(HouseResponse(
                    id=int(d.get("ID", 0)),
                    title=d.get("TITLE", "Без названия"),
                    address=d.get("UF_CRM_1669561599956") or d.get("TITLE") or "",
                    brigade=d.get("ASSIGNED_BY_NAME", "") or "Бригада не назначена",
                    management_company=d.get("COMPANY_TITLE", ""),
                    status=d.get("STAGE_ID") or "",
                    apartments=int(d.get("UF_CRM_1669704529022") or 0),
                    entrances=int(d.get("UF_CRM_1669705507390") or 0),
                    floors=int(d.get("UF_CRM_1669704631166") or 0),
                    cleaning_dates={},
                    periodicity="индивидуальная",
                    bitrix_url=f"{base_url}/crm/deal/details/{d.get('ID')}/"
                ))
            total_count = len(houses)
            pages = (total_count + limit - 1) // limit
            start = (page - 1) * limit
            end = start + limit
            return HousesResponse(houses=houses[start:end], total=total_count, page=page, limit=limit, pages=pages)</new>
</content_replace>
</file>