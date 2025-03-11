from optibook.synchronous_client import Exchange
import time
import logging

logger = logging.getLogger('client')
logger.setLevel('ERROR')

print("Setup was successful.")

exchange = Exchange()
exchange.connect()

INSTRUMENT_A = "PHILIPS_A"
INSTRUMENT_B = "PHILIPS_B"
MAX_POSITION = 200
HEDGE_TOLERANCE = 3  # Allowable range for the combined hedge
HEDGE_ACTION_LIMIT = 9  # Limit beyond which corrective action is prioritized
MIN_SPREAD = 0.2  # Minimum spread to consider arbitrage
TRADE_SIZE = 10  # Number of units to trade per opportunity
SLEEP_TIME = 0.5  # Reduced sleep time for faster responsiveness

def get_order_books():
    book_a = exchange.get_last_price_book(INSTRUMENT_A)
    book_b = exchange.get_last_price_book(INSTRUMENT_B)
    return book_a, book_b

def cancel_conflicting_orders():
    """Cancel orders that might lead to self-trades."""
    outstanding_orders_a = exchange.get_outstanding_orders(INSTRUMENT_A)
    outstanding_orders_b = exchange.get_outstanding_orders(INSTRUMENT_B)

    for order_id, order in outstanding_orders_a.items():
        exchange.cancel_order(INSTRUMENT_A, order_id)
        print(f"Canceled conflicting order in {INSTRUMENT_A}: {order}")

    for order_id, order in outstanding_orders_b.items():
        exchange.cancel_order(INSTRUMENT_B, order_id)
        print(f"Canceled conflicting order in {INSTRUMENT_B}: {order}")

def manage_positions():
    positions = exchange.get_positions()
    pos_a = positions.get(INSTRUMENT_A, 0)
    pos_b = positions.get(INSTRUMENT_B, 0)
    combined_hedge = pos_a + pos_b

    print(f"Current Positions: {positions} | Combined Hedge: {combined_hedge}")

    # If the combined hedge is within the tolerance range, do nothing
    if -HEDGE_TOLERANCE <= combined_hedge <= HEDGE_TOLERANCE:
        print(f"Hedge is within the tolerance range ({-HEDGE_TOLERANCE} to {HEDGE_TOLERANCE}). No action needed.")
        return pos_a, pos_b

    # If combined hedge drops below -HEDGE_ACTION_LIMIT, prioritize buying
    if combined_hedge < -HEDGE_ACTION_LIMIT:
        print(f"Combined Hedge ({combined_hedge}) is below -{HEDGE_ACTION_LIMIT}. Prioritizing buying...")
        best_ask_a = exchange.get_last_price_book(INSTRUMENT_A).asks[0].price
        volume = TRADE_SIZE
        exchange.insert_order(INSTRUMENT_A, price=best_ask_a, volume=volume, side="bid", order_type="ioc")
        return pos_a, pos_b

    # If combined hedge goes above +HEDGE_ACTION_LIMIT, prioritize selling
    if combined_hedge > HEDGE_ACTION_LIMIT:
        print(f"Combined Hedge ({combined_hedge}) is above +{HEDGE_ACTION_LIMIT}. Prioritizing selling...")
        best_bid_b = exchange.get_last_price_book(INSTRUMENT_B).bids[0].price
        volume = TRADE_SIZE
        exchange.insert_order(INSTRUMENT_B, price=best_bid_b, volume=volume, side="ask", order_type="ioc")
        return pos_a, pos_b

    # Handle cases where hedge is outside tolerance but not extreme
    if combined_hedge < -HEDGE_TOLERANCE:
        print(f"Combined Hedge ({combined_hedge}) below tolerance. Gradually buying to balance.")
        best_ask_a = exchange.get_last_price_book(INSTRUMENT_A).asks[0].price
        volume = TRADE_SIZE
        exchange.insert_order(INSTRUMENT_A, price=best_ask_a, volume=volume, side="bid", order_type="ioc")
    elif combined_hedge > HEDGE_TOLERANCE:
        print(f"Combined Hedge ({combined_hedge}) above tolerance. Gradually selling to balance.")
        best_bid_b = exchange.get_last_price_book(INSTRUMENT_B).bids[0].price
        volume = TRADE_SIZE
        exchange.insert_order(INSTRUMENT_B, price=best_bid_b, volume=volume, side="ask", order_type="ioc")

    return pos_a, pos_b

def calculate_opportunity(book_a, book_b):
    if book_a and book_a.bids and book_b.asks:
        best_bid_a = book_a.bids[0].price
        best_ask_b = book_b.asks[0].price
        if best_bid_a > best_ask_b + MIN_SPREAD:
            print(f"Opportunity: Sell {INSTRUMENT_A} at {best_bid_a}, Buy {INSTRUMENT_B} at {best_ask_b}")
            return "sell_a", "buy_b", best_bid_a, best_ask_b

    if book_a and book_a.asks and book_b.bids:
        best_ask_a = book_a.asks[0].price
        best_bid_b = book_b.bids[0].price
        if best_bid_b > best_ask_a + MIN_SPREAD:
            print(f"Opportunity: Buy {INSTRUMENT_A} at {best_ask_a}, Sell {INSTRUMENT_B} at {best_bid_b}")
            return "buy_a", "sell_b", best_ask_a, best_bid_b

    return None, None, None, None

def execute_trade(action_a, action_b, price_a, price_b):
    positions = exchange.get_positions()
    pos_a = positions.get(INSTRUMENT_A, 0)
    pos_b = positions.get(INSTRUMENT_B, 0)

    # Adjust trade size dynamically to avoid breaching limits
    max_buy_a = max(0, MAX_POSITION - pos_a)
    max_sell_a = max(0, pos_a + MAX_POSITION)
    max_buy_b = max(0, MAX_POSITION - pos_b)
    max_sell_b = max(0, pos_b + MAX_POSITION)

    trade_size_a = min(TRADE_SIZE, max_buy_a if action_a == "buy_a" else max_sell_a)
    trade_size_b = min(TRADE_SIZE, max_buy_b if action_b == "buy_b" else max_sell_b)

    # Cancel conflicting orders before placing new trades
    cancel_conflicting_orders()

    if action_a == "buy_a" and trade_size_a > 0:
        print(f"Placing Order: Buy {INSTRUMENT_A} at {price_a} (Size: {trade_size_a})")
        exchange.insert_order(INSTRUMENT_A, price=price_a, volume=trade_size_a, side="bid", order_type="ioc")
    elif action_a == "sell_a" and trade_size_a > 0:
        print(f"Placing Order: Sell {INSTRUMENT_A} at {price_a} (Size: {trade_size_a})")
        exchange.insert_order(INSTRUMENT_A, price=price_a, volume=trade_size_a, side="ask", order_type="ioc")

    if action_b == "buy_b" and trade_size_b > 0:
        print(f"Placing Order: Buy {INSTRUMENT_B} at {price_b} (Size: {trade_size_b})")
        exchange.insert_order(INSTRUMENT_B, price=price_b, volume=trade_size_b, side="bid", order_type="ioc")
    elif action_b == "sell_b" and trade_size_b > 0:
        print(f"Placing Order: Sell {INSTRUMENT_B} at {price_b} (Size: {trade_size_b})")
        exchange.insert_order(INSTRUMENT_B, price=price_b, volume=trade_size_b, side="ask", order_type="ioc")

def main():
    while True:
        try:
            print(f"\n--- Iteration at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            book_a, book_b = get_order_books()

            action_a, action_b, price_a, price_b = calculate_opportunity(book_a, book_b)
            if action_a and action_b:
                execute_trade(action_a, action_b, price_a, price_b)

            pos_a, pos_b = manage_positions()

            pnl = exchange.get_pnl()
            print(f"PnL: {pnl:.2f}")

            time.sleep(SLEEP_TIME)

        except Exception as error:
            print(f"An error occurred: {error}")
            break

if __name__ == "__main__":
    main()
