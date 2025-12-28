"""
无力解释,累昏了
"""

from ..func.nslookup import Nslookup

async def nslookup_srv(address: str) -> tuple[str, int]:
    result = await Nslookup(address).nslookup_srv()
    return result
