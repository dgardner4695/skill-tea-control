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
        self.ser = serial.Serial('/dev/serial0', baudrate=115200, dsrdtr=False, timeout=0.25)
        self.gas_level = 0
        self.rpm = 0
        self.pressure = 0
        self.locked = 'locked'
        self.engine_temp = 50
        self.inf = inflect.engine()

    @intent_handler(IntentBuilder('').require('CheckEngine').optionally('OnOff'))
    def handle_check_eng_intent(self, message):

        if 'OnOff' in message.data:
            on_off = message.data['OnOff']
        else:
            on_off = None

        self.ser.reset_input_buffer()
        if on_off is None:
            self.ser.write(b'checkengine_status\n')

            stat = self.ser.read(1)

            if stat.decode('utf-8') == '1':
                self.CE_status = 'on'
            elif stat.decode('utf-8') == '0':
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

        stat = self.ser.read(4)

        gas_int = int(stat.decode('utf-8').split()[0])
        self.gas_level = self.inf.number_to_words(round(100*(gas_int/1024)))

        self.speak_dialog('gas.level', data={'level': self.gas_level})

    @intent_handler(IntentBuilder('').require('RPMRead'))
    def handle_rpm_read_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A1\n')

        stat = self.ser.read(4)

        rpm_int = int(stat.decode('utf-8').split()[0])
        self.rpm = self.inf.number_to_words(rpm_int * 1000)

        self.speak_dialog('rpm.read', data={'measure': self.rpm})

    @intent_handler(IntentBuilder('').require('TempCheck'))
    def handle_engine_temp_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'analogread A4\n')

        stat = self.ser.read(4)

        temp_int = int(stat.decode('utf-8').split()[0])
        self.engine_temp = self.inf.number_to_words(round((temp_int / 1024) * 100))

        self.speak_dialog('engine.temp', data={'measure': self.engine_temp})

    @intent_handler(IntentBuilder('').require('WhichTire').require('TirePressure'))
    def handle_tire_pressure_intent(self, message):

        tire_string = message.data['WhichTire']
        which_tire = 'A2' if tire_string == 'left' else 'A3'
        
        self.ser.reset_input_buffer()
        self.ser.write('analogread {}\n'.format(which_tire).encode())

        stat = self.ser.read(4)

        pressure_int = int(stat.decode('utf-8').split()[0])
        self.pressure = self.inf.number_to_words(round((pressure_int / 1024) * 35))

        self.speak_dialog('tire.pressure', data={'whichtire': tire_string, 'pressure': self.pressure})

    @intent_handler(IntentBuilder('').require('HeadlightControl').require('OnOff'))
    def handle_headlight_intent(self, message):

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
    def handle_headlight_intent(self, message):
        
        self.ser.reset_input_buffer()
        self.ser.write(b'digitalread 12\n')

        stat = self.ser.read(1)

        if stat.decode('utf-8') == '1':
            self.locked = 'locked'
        else:
            self.locked = 'unlocked'

        self.speak_dialog('locked.unlocked', data={'state': self.locked})

    def stop(self):
        if (self.ser.isOpen()):
            self.ser.close()
        return True

def create_skill():
    return TeaControlSkill()
