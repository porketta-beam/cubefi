from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from typing import List, Optional

app = FastAPI()

# origins에 프론트엔드 주소(http://localhost:3000)를 명시적으로 추가합니다.
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/api/dividend/us-dividends')
async def get_us_dividends(tickers: Optional[str] = Query(None)):
    """
    미국 주식 티커 목록에 대한 배당 정보를 가져오는 API 엔드포인트입니다.
    티커 목록은 쿼리 파라미터로 전달할 수 있습니다. (예: ?tickers=AAPL,MSFT)
    """
    default_tickers = ['AAPL', 'MSFT', 'JNJ', 'PG', 'KO', 'CONY', 'NVDA']
    
    if tickers:
        ticker_list = [ticker.strip().upper() for ticker in tickers.split(',')]
    else:
        ticker_list = default_tickers

    dividend_data = []
    
    print(f"Fetching dividend data for: {ticker_list}")

    for ticker_symbol in ticker_list:
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            ex_dividend_date = info.get('exDividendDate')
            if ex_dividend_date:
                ex_dividend_date_str = pd.to_datetime(ex_dividend_date, unit='s').strftime('%Y-%m-%d')
            else:
                dividends = stock.dividends
                if not dividends.empty:
                    ex_dividend_date_str = dividends.index[-1].strftime('%Y-%m-%d')
                else:
                    ex_dividend_date_str = "N/A"

            dividend_yield = info.get('dividendYield')
            dividend_yield_str = f"{(dividend_yield * 100):.2f}%" if dividend_yield else "N/A"

            last_dividend_value = info.get('lastDividendValue')
            last_dividend_value_str = f"${last_dividend_value:.2f}" if last_dividend_value else "N/A"
            
            logo_map = {
                'AAPL': '🍎', 'MSFT': '💻', 'JNJ': '💊', 'PG': '🧴', 
                'KO': '🥤', 'CONY': '🚗', 'NVDA': '📈'
            }

            stock_info = {
                'code': ticker_symbol,
                'name': info.get('shortName', ticker_symbol),
                'logo': logo_map.get(ticker_symbol, '🏢'),
                'exDate': ex_dividend_date_str,
                'payMonth': "분기배당",
                'amount': last_dividend_value_str,
                'yield': dividend_yield_str,
            }
            dividend_data.append(stock_info)
            print(f"✅ Successfully fetched data for {ticker_symbol}")

        except Exception as e:
            print(f"❌ Error fetching data for {ticker_symbol}: {e}")

    return {'success': True, 'data': dividend_data}

if __name__ == '__main__':
    import uvicorn
    # DividendCalendar.js에서 8001 포트로 요청하므로 포트를 8001로 설정합니다.
    uvicorn.run(app, host='0.0.0.0', port=8001) 