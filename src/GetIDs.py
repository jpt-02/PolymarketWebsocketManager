import requests
import ast

def market_from_slug(slug):
    # Gamma API endpoint for fetching market by its URL slug
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        #ast.literal_eval is necessary because otherwise its a string of IDs, not a list of strings
        upID, downID = ast.literal_eval(data['clobTokenIds'])
        conditionID = data['conditionId']
        question = data['question']
        
        return question, conditionID, upID, downID
    else:
        print("Error fetching market data")
        return None



if __name__ == "__main__":
    slug = "btc-updown-15m-1771519500"
    print(market_from_slug(slug))