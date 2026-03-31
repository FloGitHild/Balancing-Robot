import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from datetime import datetime
import math
import time

# --- Hilfsfunktion: Winkel → Punkt ---
def winkel_zu_punkt(winkel_grad, radius):
    theta = math.radians(winkel_grad)
    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    return x, y

# --- Plot initialisieren ---
plt.ion()  # interaktiver Modus an
fig, ax = plt.subplots(figsize=(7, 7))

while plt.fignum_exists(fig.number):    

    ax.clear()  # Plot löschen
    #--- Uhrzeit lesen ---
    jetzt = datetime.now()
    stunden = jetzt.hour % 12
    minuten = jetzt.minute
    
    # --- Winkel berechnen ---
    winkel_min = 90 + (minuten * -6)
    winkel_std = 90 + (stunden * -30) + (minuten * -0.5)
    

    # --- Punkte berechnen (mit -90° Drehung für "oben") ---
    P0 = (0, 0)
    P_std = winkel_zu_punkt(winkel_std, 5)
    P_min = winkel_zu_punkt(winkel_min, 10)

    punkte = np.array([P_std, P0, P_min])

    # --- Spline erzeugen ---
    t = np.arange(len(punkte))
    spl_x = CubicSpline(t, punkte[:, 0])
    spl_y = CubicSpline(t, punkte[:, 1])

    t_fein = np.linspace(0, len(punkte)-1, 300)
    x_spline = spl_x(t_fein)
    y_spline = spl_y(t_fein)

    # --- Kreis außen (Radius 11) ---
    winkel = np.linspace(0, 2 * np.pi, 400)
    ax.plot(11 * np.cos(winkel), 11 * np.sin(winkel), linewidth=2)
    ax.plot(0.25 * np.cos(winkel), 0.25 * np.sin(winkel), linewidth=2)

    # --- Spline zeichnen ---
    ax.plot(x_spline, y_spline, linewidth=2)

    # --- Ziffern einzeichnen ---
    for z in range(1, 13):
        w = (z * -30) + 90
        x, y = winkel_zu_punkt(w, 9.5)
        ax.text(x, y, str(z), ha='center', va='center', fontsize=14)

    # --- Anzeige formatieren ---
    ax.axis("equal")
    ax.axis("off")

    plt.draw()
    plt.pause(0.1)  # kurz rendern lassen
print("Fenster wurde geschlossen")