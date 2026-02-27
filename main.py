"""
קובץ ראשי להרצת בוט הקריפטו
"""

from crypto_bot import CryptoBot
import sys


def main():
    """פונקציה ראשית"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║           🤖 בוט קריפטו - ניתוח טכני                  ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    bot = CryptoBot()
    
    # בדיקת חיבור
    print("🔌 בודק חיבור לבורסה...")
    if not bot.test_connection():
        print("\n❌ לא ניתן להתחבר לבורסה.")
        print("📝 ודא שהזנת את מפתחות ה-API ב-config.py")
        sys.exit(1)
    
    # בחירת מצב פעולה
    print("\n" + "="*60)
    print("בחר מצב פעולה:")
    print("1. ניתוח חד-פעמי (עם גרף)")
    print("2. לולאה רציפה (בדיקה כל שעה)")
    print("3. יציאה")
    print("="*60)
    
    choice = input("\nהזן בחירה (1/2/3): ").strip()
    
    if choice == '1':
        print("\n🔍 מריץ ניתוח חד-פעמי...")
        bot.run_analysis(plot=True)
        
    elif choice == '2':
        print("\n🚀 מתחיל לולאה רציפה...")
        bot.run_loop()
        
    elif choice == '3':
        print("👋 להתראות!")
        sys.exit(0)
        
    else:
        print("❌ בחירה לא תקינה")
        sys.exit(1)


if __name__ == "__main__":
    main()

