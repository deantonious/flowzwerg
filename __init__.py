from st3m.application import Application, ApplicationContext
from st3m.input import InputState
from ctx import Context
import st3m.run
import network
import urequests as requests

class FlowZwerg(Application):
    
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        self.button_status = 0
        self.temperature = 0
        self.humidity = 0
        self.air_preassure = 0
        self.uv_index = 0
        self.sound_pressure = 0
        self.dew_point = 0
        self.round_decimals = 0
        self.gnome_data = {}

        self.last_update = 0
        self.load_status = 0
        self.current_gnome = 0

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.check_connection()
        self.update_data()

    def draw(self, ctx: Context) -> None:
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 30
        ctx.font = ctx.get_font_name(1)
        ctx.save()
        ctx.move_to(0, -80).rgb(255, 255, 255).text('GnomeData')
        ctx.font_size = 24
        ctx.move_to(0, -50).rgb(255, 255, 255).text(str(self.gnomes_list[self.current_gnome]).upper())
        ctx.font_size = 16
        ctx.save()

        if self.load_status == 1:
            ctx.move_to(0, 100).rgb(255, 255, 255).text('o')

        ctx.image('/flash/sys/apps/flowzwerg/temperature.png', -100, -35, 48, 48)
        temperature = self.gnome_data[self.gnomes_list[self.current_gnome]]['temperature']
        ctx.move_to(-75, 25).rgb(255, 255, 255).text(f'{temperature} °C')

        ctx.image('/flash/sys/apps/flowzwerg/humidity.png', -50, -35, 48, 48)
        humidity = self.gnome_data[self.gnomes_list[self.current_gnome]]['humidity']
        ctx.move_to(-25, 25).rgb(255, 255, 255).text(f'{humidity} %')
        
        ctx.image('/flash/sys/apps/flowzwerg/sound_pressure.png', 0, -35, 48, 48)
        sound_pressure = self.gnome_data[self.gnomes_list[self.current_gnome]]['sound_pressure']
        ctx.move_to(25, 25).rgb(255, 255, 255).text(f'{sound_pressure} dB')

        ctx.image('/flash/sys/apps/flowzwerg/uv_index.png', 50, -35, 48, 48)
        uv_index = self.gnome_data[self.gnomes_list[self.current_gnome]]['uv_index']
        ctx.move_to(75, 25).rgb(255, 255, 255).text(f'{uv_index}')

        ctx.image('/flash/sys/apps/flowzwerg/air_pressure.png', -50, 35, 48, 48)
        air_preassure = self.gnome_data[self.gnomes_list[self.current_gnome]]['air_preassure']
        ctx.move_to(-10, 95).rgb(255, 255, 255).text(f'{air_preassure}\nmbar')

        ctx.image('/flash/sys/apps/flowzwerg/dew_point.png', 0, 35, 48, 48)
        dew_point = self.gnome_data[self.gnomes_list[self.current_gnome]]['dew_point']
        ctx.move_to(20, 95).rgb(255, 255, 255).text(f'{dew_point}')

        #ctx.move_to(0, 70).rgb(255, 255, 255).text(f'{self.last_update} ms')
        ctx.restore()

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        self.last_update += delta_ms
        if (self.last_update / 1000) > 60 * 5:
            self.last_update = 0
            self.update_data()

        direction = ins.buttons.app

        if direction == ins.buttons.PRESSED_RIGHT and self.button_status == 0:
            self.button_status = 1
        
        if direction == ins.buttons.NOT_PRESSED and self.button_status == 1:
            self.current_gnome += 1
            if self.current_gnome <= 0: 
                self.current_gnome = len(self.gnomes_list)-1
            if self.current_gnome > len(self.gnomes_list)-1: 
                self.current_gnome = 0

            self.button_status = 0
            self.last_update = 0
        

    def update_data(self) -> None:
        
        self.load_status = 1
        self.check_connection()
        query = f'from(bucket:"datagnome") |> range(start:-12h) |> last() |> drop(columns: ["_start", "_stop", "_time", "_field"])'
        headers = {
            'Accept': 'application/csv', 
            'Authorization': 'Bearer 5amv72PFZxPmnbUISjntEVxtElDYMhkeofg9Deo1ykO6Zy2XIba_iWPcyxyAp_R0dHsvHm5moE4YBCwxGIEriw==', 
            'Content-type': 'application/vnd.flux'
        }
        try:
            url = 'http://influxdb.datagnome.de:8086/api/v2/query?org=datagnome'
            res = requests.post(url, headers = headers, data = query)

            rows = res.text.rstrip().split('\n')
            rows.pop(0)
            for row in rows:
                values = row.rstrip().split(',')
                if values[5] not in self.gnome_data:
                    self.gnome_data[values[5]] = {}
                if values[4] is 'temperature':
                    self.gnome_data[values[5]]['temperature'] = round(float(values[3]))
                elif values[4] is 'humidity':
                    self.gnome_data[values[5]]['humidity'] = round(float(values[3]))
                elif values[4] is 'pressure':
                    self.gnome_data[values[5]]['air_preassure'] = round(float(values[3]))
                elif values[4] is 'uv_index':
                    self.gnome_data[values[5]]['uv_index'] = int(values[3])
                elif values[4] is 'sound_pressure':
                    self.gnome_data[values[5]]['sound_pressure'] = round(float(values[3]))
                elif values[4] is 'dew_point':
                    self.gnome_data[values[5]]['dew_point'] = round(float(values[3]))
                self.load_status = 0
        except:
            print('An exception occurred')
            self.load_status = -1
        self.gnomes_list = list(self.gnome_data.keys())
        print('Loaded gnomes: ', self.gnomes_list)
        print('Loaded gnome data: ', self.gnome_data)

    def check_connection(self) -> None:
        if not self.wlan.isconnected():          
            print('Connecting fo WiFi')
            self.wlan.connect('Camp2023-open')
            
            while not self.wlan.isconnected():
                pass
            print('Network connected: ', self.wlan.ifconfig())


if __name__ == '__main__':
    st3m.run.run_view(FlowZwerg(ApplicationContext()))