import os
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from scipy.stats import genpareto

path = "data/raw_data.shp"  # EFFIS burnt areas export, not included in the repo
data = gpd.read_file(path)
data = data[data["area_ha"] > 20]

fig_dir = "Figures"
os.makedirs(fig_dir, exist_ok=True)

TICKS = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]


def save_show(fig, name):
    fig.savefig(os.path.join(fig_dir, name), dpi=200, bbox_inches="tight")
    plt.show()


def log_axis(ax, xmax):
    ax.set_xscale("log")
    t = [x for x in TICKS if x <= xmax]
    ax.set_xticks(t, [str(x) for x in t])
    ax.minorticks_off()


def stability(area, u_min=20, q=0.99, n_thresh=50, min_exc=50):
    area = np.asarray(area)
    us = np.exp(np.linspace(np.log(u_min), np.log(np.quantile(area, q)), n_thresh))
    exc = [area[area > u] - u for u in us]
    ns = np.array([len(e) for e in exc])

    keep = ns >= min_exc
    us = us[keep]
    ns = ns[keep]
    exc = [e for e, k in zip(exc, keep) if k]

    fits = [genpareto.fit(e, floc=0) for e in exc]
    xis = np.array([f[0] for f in fits])
    sigmas = np.array([f[2] for f in fits])

    return {
        "u": us,
        "n": ns,
        "mean_exc": np.array([e.mean() for e in exc]),
        "xi": xis,
        "sigma_star": sigmas - xis * us,  # modified scale, constant above a valid threshold
    }


def fit_at(area, u):
    area = np.asarray(area)
    exc = area[area > u] - u
    xi, _, sigma = genpareto.fit(exc, floc=0)
    return xi, sigma, len(exc)


def plot_hist(area, title, fname):
    fig, ax = plt.subplots()
    ax.hist(np.log(area), bins=150, density=True, edgecolor="black")
    ax.set_xlabel("Log of area (ha)")
    ax.set_ylabel("Density")
    ax.set_title(title)
    save_show(fig, fname)


def plot_mean_excess(res, title, fname):
    fig, ax = plt.subplots()
    ax.plot(res["u"], res["mean_exc"], marker="o", markersize=3)
    ax.set_xlabel("Threshold u (ha)")
    ax.set_ylabel("Mean excess e(u) (ha)")
    ax.set_title(title)
    log_axis(ax, res["u"].max())
    save_show(fig, fname)


def plot_stability(res, title, fname):
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7, 6))
    ax1.plot(res["u"], res["xi"], marker="o", markersize=3)
    ax1.set_ylabel("ξ̂ (shape)")
    ax1.set_title(title)
    ax2.plot(res["u"], res["sigma_star"], marker="o", markersize=3)
    ax2.set_ylabel("σ* = σ̂ − ξ̂·u")
    ax2.set_xlabel("Threshold u (ha)")
    log_axis(ax2, res["u"].max())
    plt.tight_layout()
    save_show(fig, fname)


#%% all countries

area_all = data["area_ha"]
res_all = stability(area_all)

plot_hist(area_all, "Density plot, all countries", "hist_all.png")
plot_mean_excess(res_all, "Mean excess plot, all countries", "mean_excess_all.png")
plot_stability(res_all, "Parameter stability plot, all countries", "stability_all.png")
print("all, u=500:", fit_at(area_all, 500))

#%% Portugal

area_pt = data.loc[data["iso2"] == "PT", "area_ha"]
res_pt = stability(area_pt)

plot_hist(area_pt, "Density plot, Portugal", "hist_PT.png")
plot_mean_excess(res_pt, "Mean excess plot, Portugal", "mean_excess_PT.png")
plot_stability(res_pt, "Parameter stability plot, Portugal", "stability_PT.png")
print("PT, u=500:", fit_at(area_pt, 500))

#%% country comparison

print(data["iso2"].value_counts())
countries = data["iso2"].value_counts().index[:4]

fig, ax = plt.subplots(figsize=(7, 4))
for c in countries:
    res = stability(data.loc[data["iso2"] == c, "area_ha"])
    ax.plot(res["u"], res["xi"], marker="o", markersize=3, label=c)
    print(c, "u=500:", fit_at(data.loc[data["iso2"] == c, "area_ha"], 500))

ax.set_xlabel("Threshold u (ha)")
ax.set_ylabel("ξ̂ (shape)")
ax.set_title("Shape parameter by country")
ax.legend()
log_axis(ax, 20000)
plt.tight_layout()
save_show(fig, "xi_by_country.png")
