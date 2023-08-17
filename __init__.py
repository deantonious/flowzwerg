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

        self.last_update = 0
        self.load_status = 0
        self.gnomes = ['Bashful', 'Doc', 'Dopey', 'Grumpy', 'Happy', 'Hefty', 'Kinky', 'Nerdy', 'Sleepy', 'Sneezy']
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
        ctx.move_to(0, -50).rgb(255, 255, 255).text(self.gnomes[self.current_gnome])
        ctx.font_size = 16
        ctx.save()
        '''
        ctx.move_to(0, -16).rgb(255, 255, 255).text(f'Temperature: {self.temperature} °C')
        ctx.move_to(0, 0).rgb(255, 255, 255).text(f'Humidity: {self.humidity} %')
        ctx.move_to(0, 16).rgb(255, 255, 255).text(f'Presure: {self.air_preassure} mbar')
        ctx.move_to(0, 32).rgb(255, 255, 255).text(f'UV Index: {self.uv_index}')
        ctx.move_to(0, 48).rgb(255, 255, 255).text(f'Sound Presure: {self.sound_pressure} dB')
        ctx.move_to(0, 70).rgb(255, 255, 255).text(f'Last Update: {self.last_update} ms')
        '''
        if self.load_status == 1:
            ctx.move_to(0, 100).rgb(255, 255, 255).text('o')
        ctx.image('/flash/sys/apps/flow3rzwerg/temperature.png', -100, -35, 48, 48)
        ctx.move_to(-75, 25).rgb(255, 255, 255).text(f'{self.temperature} °C')
        ctx.image('/flash/sys/apps/flow3rzwerg/humidity.png', -50, -35, 48, 48)
        ctx.move_to(-25, 25).rgb(255, 255, 255).text(f'{self.humidity} %')
        ctx.image('/flash/sys/apps/flow3rzwerg/sound_pressure.png', 0, -35, 48, 48)
        ctx.move_to(25, 25).rgb(255, 255, 255).text(f'{self.sound_pressure} dB')
        ctx.image('/flash/sys/apps/flow3rzwerg/uv_index.png', 50, -35, 48, 48)
        ctx.move_to(75, 25).rgb(255, 255, 255).text(f'{self.uv_index}')


        ctx.image('/flash/sys/apps/flow3rzwerg/air_pressure.png', -50, 35, 48, 48)
        ctx.move_to(-10, 95).rgb(255, 255, 255).text(f'{self.air_preassure}\nmbar')
        ctx.image('/flash/sys/apps/flow3rzwerg/dew_point.png', 0, 35, 48, 48)
        ctx.move_to(20, 95).rgb(255, 255, 255).text(f'{self.dew_point}')

        #ctx.move_to(0, 70).rgb(255, 255, 255).text(f'{self.last_update} ms')
        ctx.restore()

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        self.last_update += delta_ms
        if (self.last_update / 1000) > 10:
            
            self.update_data()
            self.last_update = 0

        direction = ins.buttons.app

        if direction == ins.buttons.PRESSED_RIGHT and self.button_status == 0:
            self.button_status = 1
        
        if direction == ins.buttons.NOT_PRESSED and self.button_status == 1:
            self.current_gnome += 1
            if self.current_gnome <= 0: 
                self.current_gnome = len(self.gnomes)-1
            if self.current_gnome > len(self.gnomes)-1: 
                self.current_gnome = 0

            self.button_status = 0
            self.update_data()
            self.last_update = 0

    def update_data(self) -> None:
        
        self.load_status = 1
        self.check_connection()
        query = f'from(bucket:"datagnome") |> range(start:-30m) |> filter(fn:(r) => r.device == "{self.gnomes[self.current_gnome].lower()}") |> last() |> drop(columns: ["_start", "_stop", "_time", "_field"])'
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
                values = row.split(',')
                if values[4] is 'temperature':
                    self.temperature = round(float(values[3]))
                elif values[4] is 'humidity':
                    self.humidity = round(float(values[3]))
                elif values[4] is 'pressure':
                    self.air_preassure = round(float(values[3]))
                elif values[4] is 'uv_index':
                    self.uv_index = int(values[3])
                elif values[4] is 'sound_pressure':
                    self.sound_pressure = round(float(values[3]))
                elif values[4] is 'dew_point':
                    self.dew_point = round(float(values[3]))
                self.load_status = 0
        except:
            print('An exception occurred')
            self.load_status = -1

    def check_connection(self) -> None:
        if not self.wlan.isconnected():          
            print('Connecting fo WiFi')
            self.wlan.connect('Camp2023-open')
            
            while not self.wlan.isconnected():
                pass
            print('Network connected: ', self.wlan.ifconfig())


if __name__ == '__main__':
    st3m.run.run_view(FlowZwerg(ApplicationContext()))