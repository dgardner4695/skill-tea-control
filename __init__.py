# TODO: Add an appropriate license to your skill before publishing.  See
# the LICENSE file for more information.

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
import serial
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
        self.ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, dsrdtr=False, timeout=2)
        self.gas_level = 0
        self.rpm = 0
        self.pressure = 0
        self.locked = 'locked'
        self.engine_temp = 50
        self.inf = inflect.engine()

    def read_until_prompt(self, command):

        ### Do SEND
        self.ser.reset_input_buffer()
        self.ser.write(command)

        response = ''
        retry = 0

        while True:
            response += self.ser.read().decode('utf-8')
            if 'm3>' in response:
                if 'SPI bus timeout' in response:
                    result = None
                    response = ''
                    retry += 1
                    if retry > 1:
                        break
                    self.ser.reset_input_buffer()
                    self.ser.write(command)
                    continue
                result = response.split()[1]
                break
            elif len(response) == 0:
                result = None
                break
        return result

    @intent_handler(IntentBuilder('').require('CheckEngine').optionally('OnOff'))
    def handle_check_eng_intent(self, message):

        if 'OnOff' in message.data:
            on_off = message.data['OnOff']
        else:
            on_off = None

        self.ser.reset_input_buffer()
        if on_off is None:

            stat = self.read_until_prompt(b'show_pid 01\n')

            if stat is None:
                self.speak_dialog('tea.error')
                return

            self.CE_status = 'on' if stat[0] == '1' else 'off'

        else:
            self.read_until_prompt(b'clear_dtcs\n')
            self.CE_status = 'off'
            self.speak('Check engine light set to {}'.format(on_off))

        self.speak_dialog('ce.status', data={'status': self.CE_status})

    @intent_handler(IntentBuilder('').require('GasLevel'))
    def handle_gas_level_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 2f\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.gas_level = self.inf.number_to_words(stat)

        self.speak_dialog('gas.level', data={'level': self.gas_level})

    @intent_handler(IntentBuilder('').require('RPMRead'))
    def handle_rpm_read_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 0c\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.rpm = self.inf.number_to_words(stat)

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

    @intent_handler(IntentBuilder('').require('TempCheck'))
    def handle_engine_temp_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 05\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        self.engine_temp = self.inf.number_to_words(stat)

        self.speak_dialog('engine.temp', data={'measure': self.engine_temp})

    @intent_handler(IntentBuilder('').require('EngineLoad'))
    def handle_engine_load_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 04\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        load_percent = self.inf.number_to_words(stat)

        self.speak_dialog('engine.load', data={'percent': load_percent})

    @intent_handler(IntentBuilder('').require('FreezeDTC'))
    def handle_freeze_dtc_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write('analogread {}\n'.format(which_tire).encode())

        stat = self.read_until_prompt()

        if stat is None:
            self.speak_dialog('tea.error')
            return

        # freeze_dtc_code = self.inf.number_to_words(stat)

        self.speak_dialog('freeze.dtc', data={'dtc': stat})

    @intent_handler(IntentBuilder('').require('VehicleSpeed'))
    def handle_vehicle_speed_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 0d\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        speed_kmh = self.inf.number_to_words(stat)

        self.speak_dialog('vehicle.speed', data={'kmh': speed_kmh})

    @intent_handler(IntentBuilder('').require('FuelEconomy'))
    def handle_fuel_economy_intent(self, message):

        stat_VSS = self.read_until_prompt(b'show_pid 0d\n')
        stat_MAF = self.read_until_prompt(b'show_pid 10\n')

        if stat_VSS is None or stat_MAF is None or float(stat_MAF) <= 0:
            self.speak_dialog('tea.error')
            return

        econ = self.inf.number_to_words(710.7*stat_VSS/stat_MAF)

        self.speak_dialog('fuel.economy', data={'mpg': econ})

    @intent_handler(IntentBuilder('').require('EngineRuntime'))
    def handle_engine_runtime_intent(self, message):

        stat = self.read_until_prompt(b'show_pid 1f\n')

        if stat is None:
            self.speak_dialog('tea.error')
            return

        time_s = self.inf.number_to_words(stat)

        self.speak_dialog('engine.runtime', data={'time_s': time_s})

    def stop(self):
        if (self.ser.isOpen()):
            self.ser.close()
        return True

def create_skill():
    return TeaControlSkill()
