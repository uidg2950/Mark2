from keyring_variables import *


user = {
    "win_user_name": UID,
    "win_user_passwd": WIN_PASSWD
}

jira = {
    "api_search_url": "https://ix.jira.automotive.cloud/rest/api/2/search?",
    "user": user["win_user_name"],
    "passwd": user["win_user_passwd"],
}

jazz = {
    "base_url": "https://jazz.conti.de/qm1",
    "project_area": "_3NJ8QTmwEem4Jfbv6dwKcA",
    "oslc_config_context": "_xdaQoFakEeqoT5HVUFpg0A",
    "auth_url": "https://jazz.conti.de/jts/authenticated/identity",
    "user": user["win_user_name"],
    "passwd": user["win_user_passwd"],
    "headers": {
        "OSLC-Core-Version": "2.0",
        "Accept": "application/xml",
        "Content-Type": "application/rdf+xml"
    }
}

github = {
    "user": user["win_user_name"],
    "access_token": GITHUB_TOKEN,
    "output_file": "kpi_data.xlsx"
}

klocwork = {
    "user": KLOCWORK_USER,
    "token": KLOCWORK_TOKEN,
    "url": "https://dpas007x.dp.us.conti.de:8092/review/api",
    "header": {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    "project": "ConMod_Conti_Pckgs_sa515m_3y"
}

