# src/value.py
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class Params:
    """Asumsi bisnis. Nilai awal HARUS sama dengan docs/assumptions.md."""
    margin: float = 0.40          # margin kontribusi
    horizon: int = 12             # bulan
    save_rate: float = 0.25       # peluang promo menahan calon churner (ASUMSI)
    contact_cost: float = 2_000   # Rp per orang yang dihubungi
    incentive_cost: float = 10_000  # Rp per penerima insentif
    takeup: float = 0.30          # persen yang menebus insentif

    @property
    def eff_cost(self) -> float:
        """Biaya yang diharapkan per orang yang dihubungi."""
        return self.contact_cost + self.takeup * self.incentive_cost

def add_value(df: pd.DataFrame, p: Params = Params(), p_col: str = "p_churn") -> pd.DataFrame:
    out = df.copy()
    out["clv"] = out["monthly_charge"] * p.margin * p.horizon
    out["saved_value"] = out[p_col] * p.save_rate * out["clv"]   # nilai yang diharapkan diselamatkan
    out["cost"] = p.eff_cost
    out["ev"] = out["saved_value"] - out["cost"]                 # untung bersih diharapkan
    out["break_even_p"] = p.eff_cost / (p.save_rate * out["clv"])  # peluang minimum agar layak
    return out