
# ***************************************************************
# File-Name: va_gen.py
# Author: Zhang Shen
# Email: zhangshen@shanghaitech.edu.cn
# Time: 2021/09/29
# Version: V-0.1
# Usage: Automatically generate the veriloga file used to
#        generating the wave according to your input.
# ***************************************************************



class Signal:
    def __init__(self, name = 'signal', width = 1, length = 1, waves = [0]):
        self.name   = name
        self.width  = width
        self.length = length
        self.waves  = waves
        
        self.signal_name    = 'signal_{}'.format(self.name)
        self.count_name     = 'count_{}'.format(self.name)
        self.wave_name      = "wave_{}".format(self.name)
        
        self.width_declaration      = self.get_width_declaration()
        self.length_declaration     = self.get_length_declaration()

        self.input_declaration      = ''
        self.output_declaration     = self.get_output_declaration()
        self.signal_declaration     = self.get_signal_declaration()
        self.count_declaration      = self.get_count_declaration()
        self.wavelist_declaration   = self.get_wavelist_declaration()
        self.signal_initial         = self.get_signal_initial()
        self.count_initial          = self.get_count_initial()
        self.signal_generate        = self.get_signal_generate()
        self.count_generate         = self.get_count_generate()
        self.signal_output          = self.get_signal_output()

    def get_width_declaration(self):
        arg_1 = ''
        if self.width > 1:
            arg_1 = '[{}:0]'.format(self.width - 1)
        return arg_1
    
    def get_length_declaration(self):
        template = '[0:{}]'
        return template.format(self.length-1)
    
    def get_output_declaration(self):
        template = '    output {} {} ;\n    electrical {} {} ;\n'
        arg_1 = self.width_declaration
        arg_2 = self.name
        
        return template.format(arg_1, arg_2, arg_1, arg_2)
    
    def get_signal_declaration(self):
        template = '    integer {} ;'

        return template.format(self.signal_name)

    def get_count_declaration(self):
        template = '    integer {} ;'

        return template.format(self.count_name)

    def get_wavelist_declaration(self):
        template = '    integer {} {} = {} ;'
        arg_1 = self.wave_name
        arg_2 = self.length_declaration
        arg_3 = ''

        if len(self.waves) > 0 :
            arg_3 = arg_3 + '{ '
            for i in self.waves:
                arg_3 = arg_3 + ' {},'.format(i)
            arg_3 = arg_3 + ' }'
        else:
            print('ERROR!!! The length of the wave list = 0 !!!')

        return template.format(arg_1, arg_2, arg_3)

    def get_signal_initial(self):
        template = '            {} = 0 ;'
        return template.format(self.signal_name)
    
    def get_count_initial(self):
        template = '            {} = 0 ;'
        return template.format(self.count_name)

    def get_signal_generate(self):
        template = '            {} = {}[ {} % {} ] ;'
        arg_1 = self.signal_name
        arg_2 = self.wave_name
        arg_3 = self.count_name
        arg_4 = self.length

        return template.format(arg_1, arg_2, arg_3, arg_4)


    def get_count_generate(self):
        template = '            {} = {} + 1 ;'
        return template.format(self.count_name, self.count_name)

    def get_signal_output(self):
        template = '''
        for(i=0; i<{}; i=i+1) begin
            V( {} ) <+ transition( V(VDD,GND)*(({}&(1<<i))>>i), 0, 0 ) ;
        end
        '''
        arg_1 = self.width
        if(self.width) > 1:
            arg_2 = "{}[i]".format(self.name)
        else:
            arg_2 = self.name 
        arg_3 = self.signal_name
        
        return template.format(arg_1, arg_2, arg_3)

    def get_signal_grouped_output(self, bus_name, bus_offset ):
        template = '''
        for(i=0; i<{}; i=i+1) begin
            V( {}[{}+i] ) <+ transition( V(VDD,GND)*(({}&(1<<i))>>i), 0, 0 ) ;
        end
        '''
        arg_1 = self.width
        arg_2 = bus_name
        arg_3 = bus_offset
        arg_4 = self.signal_name
        return template.format(arg_1, arg_2, arg_3, arg_4)

    def get_signal_output_loop(self, bus_name=None, bus_offset=0):
        if bus_name != None:
            return self.get_signal_grouped_output(bus_name, bus_offset)
        else:
            return self.get_signal_output()

class MultiSignal:
    def __init__(self, args = [], port_groups=None):

        self.signals = self.get_signals(args=args)
        self.port_groups = port_groups or {}

        self.port_list              = self.get_port_list()
        self.input_declaration      = ''
        self.output_declaration     = self.get_output_declaration()
        self.signal_declaration     = self.get_signal_declaration()
        self.count_declaration      = self.get_count_declaration()
        self.wavelist_declaration   = self.get_wavelist_declaration()
        self.signal_initial         = self.get_signal_initial()
        self.count_initial          = self.get_count_initial()
        self.signal_generate        = self.get_signal_generate()
        self.count_generate         = self.get_count_generate()
        self.signal_output          = self.get_signal_output(port_groups=port_groups)

    def get_signals(self, args):
        thelist = []
        for arg in args:
            the_signal =  Signal(   name = arg[0],
                                    width = arg[1],
                                    length = arg[2],
                                    waves = arg[3] )
            thelist.append(the_signal)
        return thelist

    def get_port_list(self):
        ports = []
        # 1. 聚合端口
        for group_name in self.port_groups:
            ports.append(group_name)
        # 2. 非聚合的原始信号
        grouped = set(sum(self.port_groups.values(), []))
        for sig in self.signals:
            if sig.name not in grouped:
                ports.append(sig.name)
        return ', '.join(ports)

    def get_output_declaration(self):
        result = ''

        grouped = set(sum(self.port_groups.values(), []))

        # 1. group ports
        for name, members in self.port_groups.items():
            width = sum(
                sig.width for sig in self.signals if sig.name in members
            )
            result += f'    output [{width-1}:0] {name};\n'
            result += f'    electrical [{width-1}:0] {name};\n\n'
        # 2. internal member signals (NOT output!)
        for sig in self.signals:
            if sig.name in grouped:
                result += f'    electrical {sig.width_declaration} {sig.name};\n'
            else:
                result += sig.output_declaration + '\n'
        return result

    def get_signal_declaration(self):
        result = ''
        for i in self.signals:
            result = result + i.signal_declaration +'\n'
        return result

    def get_count_declaration(self):
        result = ''
        for i in self.signals:
            result = result + i.count_declaration +'\n'
        return result

    def get_wavelist_declaration(self):
        result = ''
        for i in self.signals:
            result = result + i.wavelist_declaration +'\n'
        return result

    def get_signal_initial(self):
        result = ''
        for i in self.signals:
            result = result + i.signal_initial +'\n'
        return result

    def get_count_initial(self):
        result = ''
        for i in self.signals:
            result = result + i.count_initial +'\n'
        return result

    def get_signal_generate(self):
        result = ''
        for i in self.signals:
            result = result + i.signal_generate +'\n'
        return result

    def get_count_generate(self):
        result = ''
        for i in self.signals:
            result = result + i.count_generate +'\n'
        return result  

    def get_signal_output(self, port_groups=None):
        result = ''
        signal_dict = {sig.name: sig for sig in self.signals}
        unseen_set = set( list(signal_dict.keys()) )
        if port_groups:
            for bus_name, members in port_groups.items():
                bit_offset = 0
                for member_name in reversed(members):
                    unseen_set.remove(member_name)
                    sig = signal_dict[member_name]
                    result += sig.get_signal_output_loop(bus_name, bit_offset)
                    bit_offset += sig.width

        for sig_name in unseen_set:
            sig = signal_dict[sig_name]
            result += sig.get_signal_output_loop()

        return result

class VaGenerator:
    def __init__(self, file_path):
        self.template = self.read_template(file_path=file_path)

        self.macro_list = [     '$TEMPLATE_HEAD_NOTES',
                                '$TEMPLATE_MODULE_NAME',
                                '$TEMPLATE_PORT_LIST',
                                '$TEMPLATE_INPUT_DECLARATION',
                                '$TEMPLATE_OUTPUT_DECLARATION',
                                '$TEMPLATE_SIGNAL_DECLARATION',
                                '$TEMPLATE_COUNT_DECLARATION',
                                '$TEMPLATE_WAVELIST_DECLARATION',
                                '$TEMPLATE_SIGNAL_INITIAL',
                                '$TEMPLATE_COUNT_INITIAL',
                                '$TEMPLATE_SIGNAL_GENERATE',
                                '$TEMPLATE_COUNT_GENERATE',
                                '$TEMPLATE_SIGNAL_OUTPUT',
                                ]
    def generate_veriloga(self, module_name, comment, args, save_path, port_groups=None):
        self.module_name = module_name
        self.comment = comment
        self.generate_signals(args=args, port_groups=port_groups)
        self.fill_template()
        self.save_file(file_path=save_path)

    def read_template(self, file_path='./template.va'):
        with open(file_path,"r") as f: 
            str_template = f.read()
        return str_template 

    def generate_signals(self, args, port_groups):
        thesignals = MultiSignal(args=args, port_groups=port_groups)
        self.signals = [    self.comment,
                            self.module_name,
                            thesignals.port_list,
                            thesignals.input_declaration ,
                            thesignals.output_declaration ,
                            thesignals.signal_declaration ,
                            thesignals.count_declaration ,
                            thesignals.wavelist_declaration ,
                            thesignals.signal_initial ,
                            thesignals.count_initial ,
                            thesignals.signal_generate ,
                            thesignals.count_generate ,
                            thesignals.signal_output ,
                            ]

    def fill_template(self):
        content = self.template
        for i in range(len(self.macro_list)):
            content = content.replace( self.macro_list[i], self.signals[i] )
        self.veriloga = content

    def save_file(self,file_path='generated.va'):  
        with open(file_path,"w") as f:
            f.write(self.veriloga)

