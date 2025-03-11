
Optiver Algorithmic Trading Bot

Description 
This project implements an algorithmic trading bot for the Optiver platform using Python and the Optibook API.
The bot identifies and exploits arbitrage opportunities between two financial instruments (`PHILIPS_A` and `PHILIPS_B`) while actively managing risk and position limits.  
The bot operates in real-time, competing against other teams to maximize profit by executing trades efficiently.

Features
- Arbitrage Detection – Identifies profitable trading opportunities based on price spreads.  
- Automated Order Execution – Places buy and sell orders dynamically to capture market inefficiencies.  
- Risk Management – Ensures hedging within predefined limits to minimize exposure.  
- Conflict Resolution – Cancels conflicting orders to prevent self-trading.  
- Real-time Monitoring – Continuously tracks positions, PnL, and market conditions.  

Technologies Used  
- Python
- Optibook API  
- Algorithmic Trading Strategies  

How to Run
1. Connect to the Optibook exchange.  
2. Run 'main.py' to start trading.  
3. The bot will continuously monitor market conditions and execute trades accordingly.  

