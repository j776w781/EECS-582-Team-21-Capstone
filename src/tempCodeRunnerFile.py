
@app.route('/')
def index():
    now_chi = datetime.now(ZoneInfo("America/Chicago"))
    current_time = now_chi.strftime('%H:%M')
    current_day = now_chi.strftime('%a')  # Returns Mon, Tue, Wed, etc.
    current_date = now_chi.strftime('%Y-%m-%d')
    return render_template('index.html', current_time=current_time, current_day=current_day, current_date=current_date)

# Route to display the parking permit description page