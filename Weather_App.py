import requests
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import json
import os

# ========== CONFIG ==========
API_KEY = "8f8f2c48ab094dd2ada150417252009"
BASE_URL = "http://api.weatherapi.com/v1"
FAVORITES_FILE = "favorites.json"

# ========== APP CLASS ==========
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("750x550")
        self.root.configure(bg="#eaf6f6")

        # Default settings
        self.city = "auto:ip"  # Detect location automatically
        self.unit = "C"  # Start with Celsius

        # Top frame for search + pin
        top_frame = tk.Frame(root, bg="#eaf6f6")
        top_frame.pack(pady=10)

        self.city_entry = tk.Entry(top_frame, font=("Arial", 14), width=25)
        self.city_entry.grid(row=0, column=0, padx=5)

        tk.Button(top_frame, text="Search", command=self.fetch_weather, bg="#4da6ff", fg="white").grid(row=0, column=1, padx=5)

        tk.Button(top_frame, text="Pin City", command=self.pin_city, bg="#33cc33", fg="white").grid(row=0, column=2, padx=5)

        # Favorites dropdown
        self.favorites = self.load_favorites()
        self.selected_fav = tk.StringVar()
        self.fav_dropdown = ttk.Combobox(top_frame, textvariable=self.selected_fav, values=self.favorites, state="readonly", width=15)
        self.fav_dropdown.grid(row=0, column=3, padx=5)
        self.fav_dropdown.bind("<<ComboboxSelected>>", self.load_favorite_city)

        # Unit toggle
        self.unit_button = tk.Button(root, text="Switch to °F", command=self.toggle_unit, bg="#ff8533", fg="white")
        self.unit_button.pack(pady=5)

        # Current weather display
        self.weather_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
        self.weather_frame.pack(pady=10, fill="x", padx=20)

        self.city_label = tk.Label(self.weather_frame, text="", font=("Arial", 18, "bold"), bg="#ffffff")
        self.city_label.pack()

        self.temp_label = tk.Label(self.weather_frame, text="", font=("Arial", 24), bg="#ffffff")
        self.temp_label.pack()

        self.condition_label = tk.Label(self.weather_frame, text="", font=("Arial", 14), bg="#ffffff")
        self.condition_label.pack()

        self.metrics_label = tk.Label(self.weather_frame, text="", font=("Arial", 12), bg="#ffffff")
        self.metrics_label.pack()

        # Forecast frame
        self.forecast_frame = tk.Frame(root, bg="#eaf6f6")
        self.forecast_frame.pack(pady=10)

        # Load default weather
        self.fetch_weather()

    # Toggle between Celsius and Fahrenheit
    def toggle_unit(self):
        if self.unit == "C":
            self.unit = "F"
            self.unit_button.config(text="Switch to °C")
        else:
            self.unit = "C"
            self.unit_button.config(text="Switch to °F")
        self.fetch_weather()

    # Fetch weather data
    def fetch_weather(self):
        city_name = self.city_entry.get().strip()
        if not city_name:
            city_name = self.city
        self.city = city_name

        try:
            url = f"{BASE_URL}/forecast.json?key={API_KEY}&q={self.city}&days=5&aqi=no&alerts=no"
            response = requests.get(url)
            data = response.json()

            if "error" in data:
                messagebox.showerror("Error", "City not found!")
                return

            # Current weather
            location = data["location"]
            current = data["current"]

            temp_c = current["temp_c"]
            temp_f = current["temp_f"]
            condition = current["condition"]["text"]
            humidity = current["humidity"]
            wind = current["wind_kph"]

            if self.unit == "C":
                temp_display = f"{temp_c}°C"
            else:
                temp_display = f"{temp_f}°F"

            self.city_label.config(text=f"{location['name']}, {location['country']}")
            self.temp_label.config(text=temp_display)
            self.condition_label.config(text=condition)
            self.metrics_label.config(text=f"Humidity: {humidity}%   |   Wind: {wind} km/h")

            # Update self.city to proper name (not auto:ip)
            self.city = location.get("name", self.city)

            # Forecast
            for widget in self.forecast_frame.winfo_children():
                widget.destroy()

            forecast_days = data["forecast"]["forecastday"]
            row_frame = tk.Frame(self.forecast_frame, bg="#eaf6f6")
            row_frame.pack()

            for day in forecast_days:
                date = datetime.strptime(day["date"], "%Y-%m-%d")
                weekday = date.strftime("%a")
                max_c = day["day"]["maxtemp_c"]
                min_c = day["day"]["mintemp_c"]
                max_f = day["day"]["maxtemp_f"]
                min_f = day["day"]["mintemp_f"]

                if self.unit == "C":
                    temps = f"{min_c}°C / {max_c}°C"
                else:
                    temps = f"{min_f}°F / {max_f}°F"

                # Forecast card
                card = tk.Frame(row_frame, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
                card.pack(side="left", padx=5)

                tk.Label(card, text=weekday, font=("Arial", 12, "bold"), bg="#ffffff").pack()
                tk.Label(card, text=temps, font=("Arial", 10), bg="#ffffff").pack()

        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Can't connect to the internet.")

    # Save city to favorites file
    def pin_city(self):
        shown = None
        try:
            shown = self.city_label.cget("text").split(",")[0].strip()
        except Exception:
            pass

        city_to_pin = shown if shown else self.city_entry.get().strip()
        if city_to_pin and city_to_pin.lower() != "auto:ip":
            if city_to_pin not in self.favorites:
                self.favorites.append(city_to_pin)
                self.save_favorites()
                messagebox.showinfo("Pinned", f"{city_to_pin} added to favorites.")
            else:
                messagebox.showinfo("Pinned", f"{city_to_pin} is already in favorites.")
        else:
            messagebox.showwarning("Pin Error", "No valid city to pin.")

    # Load pinned city
    def load_favorite_city(self, event):
        fav_city = self.selected_fav.get()
        if fav_city:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, fav_city)
            self.fetch_weather()

    # Load favorites from file
    def load_favorites(self):
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "favorites" in data:
                    return data["favorites"]
                if isinstance(data, list):
                    return data
            except Exception:
                return []
        return []

    # Save favorites to file
    def save_favorites(self):
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
            self.fav_dropdown['values'] = self.favorites
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to save favorites: {e}")


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
