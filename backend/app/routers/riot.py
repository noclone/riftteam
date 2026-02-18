from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_riot_client
from app.schemas.player import RiotCheckResponse
from shared.riot_client import RiotAPIError

router = APIRouter(tags=["riot"])


@router.get("/riot/check/{name}/{tag}", response_model=RiotCheckResponse)
async def check_riot_id(name: str, tag: str, request: Request):
    client = get_riot_client(request)
    try:
        account = await client.get_account_by_riot_id(name, tag)
    except RiotAPIError as e:
        if e.status == 404:
            raise HTTPException(404, "Riot ID not found")
        raise HTTPException(502, f"Riot API error: {e.message}")

    puuid = account["puuid"]
    summoner_level = None
    profile_icon_id = None
    try:
        summoner = await client.get_summoner_by_puuid(puuid)
        summoner_level = summoner.get("summonerLevel")
        profile_icon_id = summoner.get("profileIconId")
    except RiotAPIError:
        pass

    return RiotCheckResponse(
        game_name=account.get("gameName", name),
        tag_line=account.get("tagLine", tag),
        puuid=puuid,
        summoner_level=summoner_level,
        profile_icon_id=profile_icon_id,
    )
