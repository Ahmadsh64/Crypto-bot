"""
בוט קריפטו - ניתוח טכני ואיתותי מסחר
"""

import ccxt
import pandas as pd
import ta
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from config import (
    EXCHANGE_NAME, API_KEY, API_SECRET, SYMBOL, TIMEFRAME, LIMIT,
    EMA_WINDOW, RSI_WINDOW, RSI_OVERSOLD, RSI_OVERBOUGHT, CHECK_INTERVAL
)


class CryptoBot:
    """בוט לניתוח טכני ומסחר בקריפטו"""
    
    def __init__(self):
        """אתחול הבוט וחיבור לבורסה"""
        self.exchange = self._init_exchange()
        self.symbol = SYMBOL
        self.timeframe = TIMEFRAME
        
    def _init_exchange(self):
        """יצירת חיבור לבורסה"""
        exchange_class = getattr(ccxt, EXCHANGE_NAME)
        exchange = exchange_class({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # או 'future' למסחר עתידי
            }
        })
        return exchange
    
    def test_connection(self):
        """בדיקת חיבור לבורסה"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            print(f"✅ חיבור מוצלח!")
            print(f"מחיר נוכחי {self.symbol}: ${ticker['last']:.2f}")
            return True
        except Exception as e:
            print(f"❌ שגיאה בחיבור: {e}")
            print("⚠️ ודא שהזנת את מפתחות ה-API ב-config.py")
            return False
    
    def fetch_data(self, limit=LIMIT):
        """קבלת נתונים היסטוריים"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            print(f"❌ שגיאה בקבלת נתונים: {e}")
            return None
    
    def calculate_indicators(self, df):
        """חישוב אינדיקטורים טכניים"""
        # EMA (ממוצע נע אקספוננציאלי)
        df['ema50'] = ta.trend.EMAIndicator(
            df['close'], window=EMA_WINDOW
        ).ema_indicator()
        
        # RSI (Relative Strength Index)
        df['rsi'] = ta.momentum.RSIIndicator(
            df['close'], window=RSI_WINDOW
        ).rsi()
        
        # MACD (אופציונלי)
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        return df
    
    def generate_signal(self, df):
        """
        יצירת איתות מסחר
        מחזיר: 'BUY', 'SELL', או 'HOLD'
        """
        if len(df) < EMA_WINDOW:
            return 'HOLD', "לא מספיק נתונים"
        
        current_price = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        current_ema = df['ema50'].iloc[-1]
        prev_rsi = df['rsi'].iloc[-2] if len(df) > 1 else current_rsi
        
        # תנאי קנייה
        buy_conditions = []
        if current_rsi < RSI_OVERSOLD:
            buy_conditions.append(f"RSI נמוך ({current_rsi:.2f} < {RSI_OVERSOLD})")
        if current_price > current_ema:
            buy_conditions.append(f"מחיר מעל EMA ({current_price:.2f} > {current_ema:.2f})")
        if current_rsi < prev_rsi:  # RSI יורד (מתקרב לנקודת קנייה)
            buy_conditions.append("RSI יורד")
        
        # תנאי מכירה
        sell_conditions = []
        if current_rsi > RSI_OVERBOUGHT:
            sell_conditions.append(f"RSI גבוה ({current_rsi:.2f} > {RSI_OVERBOUGHT})")
        if current_price < current_ema:
            sell_conditions.append(f"מחיר מתחת ל-EMA ({current_price:.2f} < {current_ema:.2f})")
        
        # קביעת איתות
        if len(buy_conditions) >= 2:
            reason = " | ".join(buy_conditions)
            return 'BUY', reason
        elif len(sell_conditions) >= 1:
            reason = " | ".join(sell_conditions)
            return 'SELL', reason
        else:
            return 'HOLD', "אין תנאים מתאימים"
    
    def plot_analysis(self, df, signal, reason):
        """ציור גרף עם ניתוח טכני"""
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        fig.suptitle(f'ניתוח טכני - {self.symbol} | איתות: {signal}', 
                     fontsize=16, fontweight='bold')
        
        # גרף 1: מחיר + EMA
        ax1 = axes[0]
        ax1.plot(df.index, df['close'], label='מחיר סגירה', linewidth=2, color='blue')
        ax1.plot(df.index, df['ema50'], label=f'EMA {EMA_WINDOW}', 
                linewidth=1.5, color='orange', linestyle='--')
        
        # סימון נקודת כניסה/יציאה
        last_idx = df.index[-1]
        last_price = df['close'].iloc[-1]
        if signal == 'BUY':
            ax1.scatter(last_idx, last_price, color='green', s=200, 
                       marker='^', label='איתות קנייה', zorder=5)
        elif signal == 'SELL':
            ax1.scatter(last_idx, last_price, color='red', s=200, 
                       marker='v', label='איתות מכירה', zorder=5)
        
        ax1.set_ylabel('מחיר (USDT)', fontsize=12)
        ax1.set_title('מחיר ואינדיקטור EMA', fontsize=14)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        
        # גרף 2: RSI
        ax2 = axes[1]
        ax2.plot(df.index, df['rsi'], label='RSI', linewidth=2, color='purple')
        ax2.axhline(y=RSI_OVERBOUGHT, color='r', linestyle='--', 
                   label=f'על-קנייה ({RSI_OVERBOUGHT})', alpha=0.7)
        ax2.axhline(y=RSI_OVERSOLD, color='g', linestyle='--', 
                   label=f'על-מכירה ({RSI_OVERSOLD})', alpha=0.7)
        ax2.axhline(y=50, color='gray', linestyle=':', alpha=0.5)
        ax2.fill_between(df.index, RSI_OVERSOLD, RSI_OVERBOUGHT, 
                         alpha=0.1, color='yellow')
        ax2.set_ylabel('RSI', fontsize=12)
        ax2.set_title('RSI Indicator', fontsize=14)
        ax2.set_ylim(0, 100)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        
        # גרף 3: MACD
        ax3 = axes[2]
        ax3.plot(df.index, df['macd'], label='MACD', linewidth=1.5, color='blue')
        ax3.plot(df.index, df['macd_signal'], label='Signal', 
                linewidth=1.5, color='red')
        ax3.bar(df.index, df['macd_diff'], label='Histogram', 
               alpha=0.3, color='gray')
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.set_ylabel('MACD', fontsize=12)
        ax3.set_title('MACD Indicator', fontsize=14)
        ax3.set_xlabel('תאריך ושעה', fontsize=12)
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        
        plt.tight_layout()
        
        # שמירת הגרף
        filename = f'analysis_{self.symbol.replace("/", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"📊 גרף נשמר: {filename}")
        
        plt.show()
    
    def run_analysis(self, plot=True):
        """הרצת ניתוח חד-פעמי"""
        print(f"\n{'='*60}")
        print(f"🔍 מתחיל ניתוח: {self.symbol} | {self.timeframe}")
        print(f"{'='*60}\n")
        
        # קבלת נתונים
        df = self.fetch_data()
        if df is None:
            return
        
        # חישוב אינדיקטורים
        df = self.calculate_indicators(df)
        
        # יצירת איתות
        signal, reason = self.generate_signal(df)
        
        # הצגת תוצאות
        print(f"📈 נתונים אחרונים:")
        print(f"   מחיר נוכחי: ${df['close'].iloc[-1]:.2f}")
        print(f"   EMA {EMA_WINDOW}: ${df['ema50'].iloc[-1]:.2f}")
        print(f"   RSI: {df['rsi'].iloc[-1]:.2f}")
        print(f"   MACD: {df['macd'].iloc[-1]:.4f}")
        print(f"\n🎯 איתות: {signal}")
        print(f"   סיבה: {reason}")
        print(f"\n📅 זמן: {df.index[-1]}")
        
        # הצגת טבלה אחרונה
        print(f"\n📊 5 הנתונים האחרונים:")
        display_cols = ['close', 'ema50', 'rsi', 'macd']
        print(df[display_cols].tail().to_string())
        
        # ציור גרף
        if plot:
            self.plot_analysis(df, signal, reason)
        
        return df, signal, reason
    
    def run_loop(self):
        """הרצת בוט בלולאה רציפה"""
        print(f"\n{'='*60}")
        print(f"🚀 בוט פועל - בדיקה כל {CHECK_INTERVAL//60} דקות")
        print(f"⏹️  לחץ Ctrl+C להפסקה")
        print(f"{'='*60}\n")
        
        try:
            while True:
                df, signal, reason = self.run_analysis(plot=False)
                
                if signal != 'HOLD':
                    print(f"\n⚠️  איתות פעיל: {signal} - {reason}")
                    # כאן אפשר להוסיף לוגיקה למסחר אמיתי
                
                print(f"\n⏳ ממתין {CHECK_INTERVAL//60} דקות לבדיקה הבאה...")
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  בוט הופסק על ידי המשתמש")
        except Exception as e:
            print(f"\n❌ שגיאה: {e}")


if __name__ == "__main__":
    bot = CryptoBot()
    
    # בדיקת חיבור
    if not bot.test_connection():
        exit(1)
    
    # הרצת ניתוח חד-פעמי
    bot.run_analysis(plot=True)

