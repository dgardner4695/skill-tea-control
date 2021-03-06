# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
import socket
import subprocess
import parseelm
import inflect
import time

# Each intent controls or accesses a specific system of the car

# TEA (Third Eye Auto) Control Skill
class TeaControlSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(TeaControlSkill, self).__init__(name='TeaControlSkill')
        
        # Initialize working variables used within the skill.
        self.CE_status = 'off'
        self.comm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.comm.connect(('localhost', 10003))
        self.gas_level = 0
        self.rpm = 0
        self.pressure = 0
        self.locked = 'locked'
        self.engine_temp = 50
        self.inf = inflect.engine()

    def send_recv_obd(self, command):
        ### Do SEND
        self.comm.send(command)
        resp = self.comm.recv(1024)

        return list(parseelm.parse_response(resp.decode('utf-8'), strict=False))

    @intent_handler(IntentBuilder('').require('CheckEngine').optionally('OnOff'))
    def handle_check_eng_intent(self, message):

        if 'OnOff' in message.data:
            on_off = message.data['OnOff']
        else:
            on_off = None

        if on_off is None:

            stat = self.send_recv_obd(b'0101\r\n')

            if stat is None:
                self.speak_dialog('tea.error')
                return

            self.CE_status = 'on' if (stat[2] & 0xf0) else 'off'

        else:
            self.send_recv_obd(b'04\r\n')
            self.CE_status = 'off'
            self.speak('Check engine light set to {}'.format(on_off))

        self.speak_dialog('ce.status', data={'status': self.CE_status})

    @intent_handler(IntentBuilder('').require('GasLevel'))
    def handle_gas_level_intent(self, message):

        stat = self.send_recv_obd(b'012f\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.gas_level = self.inf.number_to_words(int((100/255)*stat[-1]))

        self.speak_dialog('gas.level', data={'level': self.gas_level})

    @intent_handler(IntentBuilder('').require('RPMRead'))
    def handle_rpm_read_intent(self, message):

        stat = self.send_recv_obd(b'010c\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        rpm_read = (stat[-2]*256 + stat[-1])/4
        self.rpm = self.inf.number_to_words(int(rpm_read))

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

    @intent_handler(IntentBuilder('').require('TempCheck'))
    def handle_engine_temp_intent(self, message):

        stat = self.send_recv_obd(b'0105\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.engine_temp = self.inf.number_to_words(stat[-1]-40)

        self.speak_dialog('engine.temp', data={'measure': self.engine_temp})

    @intent_handler(IntentBuilder('').require('EngineLoad'))
    def handle_engine_load_intent(self, message):

        stat = self.send_recv_obd(b'0104\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        load_percent = self.inf.number_to_words(int((100/255)*stat[-1]))

        self.speak_dialog('engine.load', data={'percent': load_percent})

    @intent_handler(IntentBuilder('').require('FreezeDTC'))
    def handle_freeze_dtc_intent(self, message):

        stat = self.send_recv_obd(b'03\r\n')
        dtc = []

        if stat is None:
            self.speak_dialog('tea.error')
            return

        if len(stat) <= 3:
            self.speak('No errors found')
            return
        
        self.speak('The following error codes were found')
        for i in range(int((len(stat)-2)/2)):
            dtc.append('')
            offset = 2*i
            dtc[i] += ['P,', 'C,', 'B,', 'U,'][stat[2+offset] >> 6]
            dtc[i] += str((stat[2+offset] >> 4) & 0x3) + ','
            dtc[i] += format(stat[2+offset] & 0x3, 'x') + ','
            dtc[i] += format((stat[3+offset] >> 4) & 0xf, 'x') + ','
            dtc[i] += format(stat[3+offset] & 0xf, 'x')
            self.speak(dtc[i])


    @intent_handler(IntentBuilder('').require('VehicleSpeed'))
    def handle_vehicle_speed_intent(self, message):

        stat = self.send_recv_obd(b'010d\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        speed_kmh = self.inf.number_to_words(stat[-1])

        self.speak_dialog('vehicle.speed', data={'kmh': speed_kmh})

    @intent_handler(IntentBuilder('').require('FuelEconomy'))
    def handle_fuel_economy_intent(self, message):

        stat_VSS = self.send_recv_obd(b'010d\r\n')
        stat_MAF = self.send_recv_obd(b'0110\r\n')

        if stat_VSS is None or stat_MAF is None:
            self.speak_dialog('tea.error')
            return
        if stat_MAF[-1] <= 0:
            self.speak_dialog('tea.error')
            return
        
        vss = stat_VSS[-1]
        maf = (256 * stat_MAF[-2] + stat_MAF[-1])

        econ = self.inf.number_to_words(int(710.7*vss/maf))

        self.speak_dialog('fuel.economy', data={'mpg': econ})

    @intent_handler(IntentBuilder('').require('EngineRuntime'))
    def handle_engine_runtime_intent(self, message):

        stat = self.send_recv_obd(b'011f\r\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        time_s = self.inf.number_to_words((256 * stat[-2] + stat[-1]))

        self.speak_dialog('engine.runtime', data={'time_s': time_s})

    @intent_handler(IntentBuilder('').require('Despacito'))
    def handle_despacito_intent(self, message):

        subprocess.call(['aplay', '/home/pi/capstone/mycroft-core/despacito.wav'])

    def stop(self):
        if (self.ser.isOpen()):
            self.ser.close()
        return True

def create_skill():
    return TeaControlSkill()
