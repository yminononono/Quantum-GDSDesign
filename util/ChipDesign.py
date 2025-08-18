import sys
from qubit_templates import *
from functions import *

def chipdesign_TcSample(frequency):

    chipdesign = Device('chipdesign')

    # Frame
    FM=Device('frame')
    rectangle = pg.rectangle((Frame_size_width, Frame_size_height), Frame_layer)
    FM.add_ref( pg.invert(rectangle, border = Frame_width, precision = 1e-6, layer = Frame_layer) )
    FM.center = (0, 0)
    chipdesign.add_ref(FM)

    # Feed line
    FL = device_FeedLine()
    chipdesign.add_ref(FL.device)

    # Corner points
    CP = device_CornerPoints()
    chipdesign.add_ref(CP)

    # Resonator
    resonator_config = dict(
        resonator_straight1 = 220, 
        resonator_straight2 = 260, 
        resonator_straight3 = 475, 
        resonator_straight4 = 700, 
        n_step = 3, 
        transmon = False, 
        mirror = True, 
        print_length = True, 
        norm_to_length = calculate_resonator_length(frequency = frequency[0], material = "silicon"),
        #norm_to_length = 3250
    )

    R1 = device_Resonator(**resonator_config)
    R1.rotate(-90)
    if FeedLine_path_type == "straight":
        R1.xmin = FL.device.x + 0.5*LaunchPad_trace_width + LaunchPad_trace_gap_width + Feedline_Resonator_gap
        R1.y = 500
    elif FeedLine_path_type == "manual":
        R1.xmin = FeedLine_path_points[0][0] + 0.5*LaunchPad_trace_width + LaunchPad_trace_gap_width + Feedline_Resonator_gap
        R1.y = 0.5*(FeedLine_input_pos[1] + FeedLine_path_points[0][1])
    elif FeedLine_path_type == "extrude":
        sys.exit("Currently I don't know how to extract the right position to place the resonators...")
    chipdesign.add_ref(R1.device)

    resonator_config.update(
        resonator_straight1 = 220,
        resonator_straight2 = 260,
        resonator_straight3 = 475,
        resonator_straight4 = 1100,
        mirror = False,
        norm_to_length = calculate_resonator_length(frequency = frequency[1], material = "silicon"),
        # norm_to_length = 3700
    )

    R2 = device_Resonator(**resonator_config)
    R2.rotate(90)
    if FeedLine_path_type == "straight":
        R2.xmin = FL.device.x + 0.5*LaunchPad_trace_width + LaunchPad_trace_gap_width + Feedline_Resonator_gap
        R2.y = -500
    elif FeedLine_path_type == "manual":
        R2.xmin = FeedLine_path_points[3][0] + 0.5*LaunchPad_trace_width + LaunchPad_trace_gap_width + Feedline_Resonator_gap
        R2.y = 0.5*(FeedLine_output_pos[1] + FeedLine_path_points[3][1])
    elif FeedLine_path_type == "extrude":
        sys.exit("Currently I don't know how to extract the right position to place the resonators...")
    chipdesign.add_ref(R2.device)

    return chipdesign