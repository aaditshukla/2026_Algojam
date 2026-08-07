# AlgoJam 3

**UQ Fintech Society × IMC Trading — Algorithmic Trading Competition**

Teams write a Python algorithm that trades 9 fictional financial instruments over a simulated year, competing to maximise profit & loss (P&L) under portfolio constraints.

Full rules, dates, and submission instructions: [`docs/AlgoJam3_Event_Info.pdf`](docs/AlgoJam3_Event_Info.pdf)
Instrument stories, hints, and Round 1 charts: [`docs/AlgoJam3_Instrument_Specification.pdf`](docs/AlgoJam3_Instrument_Specification.pdf)

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Open trader_interface/algorithm.py and write your strategy inside get_positions()

# 3. Backtest it against Round 1 data
cd trader_interface
python simulation.py
```

`trader_interface/data/` contains **Round 1 only** — the historical year you can see and develop against. Your algorithm is scored on Round 2, a second simulated year you never see, revealed live during Presentation Night marking.

---

## Writing your algorithm

Open `trader_interface/algorithm.py`. Everything you need to implement is inside `get_positions()`:

```python
def get_positions(self):
    desiredPositions = {instrument: 0 for instrument in self.positionLimits}

    # Your strategy here.
    # self.day            — current day (0–364 in Round 1; resets to 0–364 again in Round 2)
    # self.data           — {instrument: [price_day0, ..., price_today]}, grows by one day at a time
    # self.positionLimits — {instrument: max_units}
    # self.positions      — your current held position per instrument

    return desiredPositions
```

**Rules:**
- All position values must be **integers**
- `|position|` must not exceed `positionLimits[instrument]`
- Total portfolio value (`Σ |position × price|`) must not exceed **$600,000 AUD** per day. For example, going short -$1000 on UQ Dollar and long $1200 on UQ Fintech Token uses $2200 of the budget.
- Violating the budget zeroes your entire position for that day

See the Instrument Specification PDF for the full rules on each instrument, including Liferaft Ticket — the one instrument whose price isn't pre-generated; it's computed live from what every team decides.

---

## Instruments

| Instrument | Position Limit |
|---|---|
| Fintech Token | 100 |
| UQ Dollar | 650 |
| Thrifted Jeans | 800 |
| Sausage Sizzle | 3,000 |
| Bread | 500 |
| MenuDash | 75,000 |
| Sausage | 5,000 |
| Liferaft Ticket | 1 |
| Boat Party Ticket | 1,000 |

Each instrument has a distinct hidden price behaviour. Part of the challenge is identifying and exploiting it — the Instrument Specification PDF has a hint for each one.

---

## Submitting

See `docs/AlgoJam3_Event_Info.pdf` for the submission email, deadline, and key dates.
