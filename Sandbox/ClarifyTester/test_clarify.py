import requests;
import json;

url = "https://labs.tib.eu/sdm/clarify-exp/kg-exp?target=DDI&limit=10&page=0";
data = {"Drugs": ["C0000970", "C0028978", "C0009214"]};

def getClarifyResponse():
    resp = requests.post(url, json=data);

    return resp.text;

if __name__ == "__main__":
    reply = getClarifyResponse();

    print (reply);