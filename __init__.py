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
        self.ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, dsrdtr=False, timeout=0.25)
        self.gas_level = 0
        self.rpm = 0
        self.pressure = 0
        self.locked = 'locked'
        self.engine_temp = 50
        self.inf = inflect.engine()

    def read_until_prompt(self):
        response = ''
        while True:
            response += self.ser.read().decode('utf-8')
            if 'm3>' in response:
                print(response)
                return response.split()[1]
            elif 'ERROR' in response:
                return 0

    @intent_handler(IntentBuilder('').require('CheckEngine').optionally('OnOff'))
    def handle_check_eng_intent(self, message):

        if 'OnOff' in message.data:
            on_off = message.data['OnOff']
        else:
            on_off = None

        self.ser.reset_input_buffer()
        if on_off is None:
            self.ser.write(b'checkengine_status\n')

            stat = self.read_until_prompt()

            if not stat:
                self.speak_dialog('error')
                return

            if stat == '1':
                self.CE_status = 'on'
            elif stat == '0':
                self.CE_status = 'off'
        else:
            self.ser.write('checkengine_light {}\n'.format(on_off).encode())
            self.CE_status = on_off
            self.speak('Check engine light set to {}'.format(on_off))

        self.speak_dialog('ce.status', data={'status': self.CE_status})

    @intent_handler(IntentBuilder('').require('GasLevel'))
    def handle_gas_level_intent(self, message):

        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A0\n')

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        self.gas_level = self.inf.number_to_words(stat)

        self.speak_dialog('gas.level', data={'level': self.gas_level})

    @intent_handler(IntentBuilder('').require('RPMRead'))
    def handle_rpm_read_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'show_pid 0c\n')

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        self.rpm = self.inf.number_to_words(stat)

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

    @intent_handler(IntentBuilder('').require('TempCheck'))
    def handle_engine_temp_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A4\n')

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        self.engine_temp = self.inf.number_to_words(stat)

        self.speak_dialog('engine.temp', data={'measure': self.engine_temp})

    @intent_handler(IntentBuilder('').require('WhichTire').require('TirePressure'))
    def handle_tire_pressure_intent(self, message):

        tire_string = message.data['WhichTire']
        which_tire = 'A2' if tire_string == 'left' else 'A3'
        
        self.ser.reset_input_buffer()
        self.ser.write('analogread {}\n'.format(which_tire).encode())

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        self.pressure = self.inf.number_to_words(stat)

        self.speak_dialog('tire.pressure', data={'whichtire': tire_string, 'pressure': self.pressure})

    @intent_handler(IntentBuilder('').require('HeadlightControl').require('OnOff'))
    def handle_headlightcontrol_intent(self, message):

        on_off = message.data['OnOff']
        
        self.ser.reset_input_buffer()
        self.ser.write('headlights {}\n'.format(on_off).encode())

        self.speak_dialog('head.light', data={'state': on_off})

    @intent_handler(IntentBuilder('').require('OpenClose').require('Windows'))
    def handle_window_adjust_intent(self, message):

        open_close = message.data['OpenClose']
        
        self.ser.reset_input_buffer()
        self.ser.write('window {}\n'.format(open_close).encode())

        self.speak_dialog('window.adjust', data={'state': open_close})

    @intent_handler(IntentBuilder('').require('LockCheck'))
    def handle_lockcheck_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'digitalread 12\n')

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        if stat == '1':
            self.locked = 'locked'
        else:
            self.locked = 'unlocked'

        self.speak_dialog('locked.unlocked', data={'state': self.locked})

    @intent_handler(IntentBuilder('').require('TirePressure'))
    def handle_tire_pressure_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write('analogread {}\n'.format(which_tire).encode())

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        load_percent = self.inf.number_to_words(stat)

        self.speak_dialog('engine.load', data={'percent': load_percent})

    @intent_handler(IntentBuilder('').require('EngineLoad'))
    def handle_engine_load_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write('show_pid 04\n'.encode())

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        load_percent = self.inf.number_to_words(stat)

        self.speak_dialog('engine.load', data={'percent': load_percent})

    @intent_handler(IntentBuilder('').require('FreezeDTC'))
    def handle_freeze_dtc_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write('analogread {}\n'.format(which_tire).encode())

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        # freeze_dtc_code = self.inf.number_to_words(stat)

        self.speak_dialog('freeze.dtc', data={'dtc': stat})

    @intent_handler(IntentBuilder('').require('VehicleSpeed'))
    def handle_vehicle_speed_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write('show_pid 0d\n'.encode())

        stat = self.read_until_prompt()

        if not stat:
            self.speak_dialog('error')
            return

        speed_kmh = self.inf.number_to_words(stat)

        self.speak_dialog('vehicle.speed', data={'kmh': speed_kmh})

    def stop(self):
        if (self.ser.isOpen()):
            self.ser.close()
        return True

def create_skill():
    return TeaControlSkill()
