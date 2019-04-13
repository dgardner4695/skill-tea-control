# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
import socket
import select
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
        ready_sock = select.select([self.comm], [], [], timeout=1)

        if ready_sock[0]:
            resp = self.comm.recv(1024)
            return list(parseelm.parse_response(resp.decode()))

        return None

    @intent_handler(IntentBuilder('').require('CheckEngine').optionally('OnOff'))
    def handle_check_eng_intent(self, message):

        if 'OnOff' in message.data:
            on_off = message.data['OnOff']
        else:
            on_off = None

        if on_off is None:

            stat = self.send_recv_obd(b'0101\n')

            if stat is None:
                self.speak_dialog('tea.error')
                return

            self.CE_status = 'on' if (stat[2] & 64) else 'off'

        else:
            self.send_recv_obd(b'0400\n')
            self.CE_status = 'off'
            self.speak('Check engine light set to {}'.format(on_off))

        self.speak_dialog('ce.status', data={'status': self.CE_status})

    @intent_handler(IntentBuilder('').require('GasLevel'))
    def handle_gas_level_intent(self, message):

        stat = self.send_recv_obd(b'012f\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.gas_level = self.inf.number_to_words((100/255)*stat[-1])

        self.speak_dialog('gas.level', data={'level': self.gas_level})

    @intent_handler(IntentBuilder('').require('RPMRead'))
    def handle_rpm_read_intent(self, message):

        stat = self.send_recv_obd(b'010c\n')
        if stat is None:
            self.speak_dialog('tea.error')
            return

        rpm_read = (stat[-2]*256 + stat[-1])/4
        self.rpm = self.inf.number_to_words(rpm_read)

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

    @intent_handler(IntentBuilder('').require('TempCheck'))
    def handle_engine_temp_intent(self, message):

        stat = self.send_recv_obd(b'0105\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.engine_temp = self.inf.number_to_words(stat[-1]-40)

        self.speak_dialog('engine.temp', data={'measure': self.engine_temp})

    @intent_handler(IntentBuilder('').require('EngineLoad'))
    def handle_engine_load_intent(self, message):

        stat = self.send_recv_obd(b'0104\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        load_percent = self.inf.number_to_words((100/255)*stat[-1])

        self.speak_dialog('engine.load', data={'percent': load_percent})

    @intent_handler(IntentBuilder('').require('FreezeDTC'))
    def handle_freeze_dtc_intent(self, message):

        stat = self.send_recv_obd(b'0300\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        # freeze_dtc_code = self.inf.number_to_words(stat)

        self.speak_dialog('freeze.dtc', data={'dtc': stat})

    @intent_handler(IntentBuilder('').require('VehicleSpeed'))
    def handle_vehicle_speed_intent(self, message):

        stat = self.send_recv_obd(b'010d\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        speed_kmh = self.inf.number_to_words(stat[-1])

        self.speak_dialog('vehicle.speed', data={'kmh': speed_kmh})

    @intent_handler(IntentBuilder('').require('FuelEconomy'))
    def handle_fuel_economy_intent(self, message):

        stat_VSS = self.send_recv_obd(b'010d\n')
        stat_MAF = self.send_recv_obd(b'0110\n')

        if stat_VSS is None or stat_MAF is None:
            self.speak_dialog('tea.error')
            return
        if stat_MAF[-1] <= 0:
            self.speak_dialog('tea.error')
            return
        
        vss = stat_VSS[-1]
        maf = (256 * stat_MAF[-2] + stat_MAF[-1])/100 

        econ = self.inf.number_to_words(710.7*vss/maf)

        self.speak_dialog('fuel.economy', data={'mpg': econ})

    @intent_handler(IntentBuilder('').require('EngineRuntime'))
    def handle_engine_runtime_intent(self, message):

        stat = self.send_recv_obd(b'011f\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        time_s = self.inf.number_to_words((256 * stat[-2] + stat[-1]))

        self.speak_dialog('engine.runtime', data={'time_s': time_s})

    def stop(self):
        if (self.ser.isOpen()):
            self.ser.close()
        return True

def create_skill():
    return TeaControlSkill()
