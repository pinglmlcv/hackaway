"""Definition of entities. Thanks to:
https://github.com/DeNA/Chainer_Realtime_Multi-Person_Pose_Estimation
"""


from enum import IntEnum


class Joint(IntEnum):
    """Joint type for pose estimation task, we define our 
    own keypoints order and joint type, which is different
    from COCO's. 

    MS COCO annotation order:
    0: nose         1: l eye        2: r eye    3: l ear    4: r ear
    5: l shoulder   6: r shoulder   7: l elbow  8: r elbow
    9: l wrist      10: r wrist     11: l hip   12: r hip   
    13: l knee      14: r knee      15: l ankle 16: r ankle

    NOTE: R means right, L means left. There are 17 parts 
    in MS COCO dataset. Following authors' implementation, 
    we compute neck position according to shoulders.
    """
    Nose = 0 
    Neck = 1 
    RShoulder = 2; RElbow = 3; RWrist = 4
    LShoulder = 5; LElbow = 6; LWrist = 7
    RHip = 8;   RKnee = 9;  RAnkle = 10
    LHip = 11;  LKnee = 12; LAnkle = 13
    REye = 14;  LEye = 15 
    REar = 16;  LEar = 17


class Params:
    pass

class KeyPointParams(Params):

    joint = Joint

    # In MS COCO, this is called skeleton
    # What we define here is different.
    limbs = [
        [Joint.Neck, Joint.RHip],
        [Joint.RHip, Joint.RKnee],
        [Joint.RKnee, Joint.RAnkle],

        [Joint.Neck, Joint.LHip],
        [Joint.LHip, Joint.LKnee],
        [Joint.LKnee, Joint.LAnkle],

        [Joint.Neck, Joint.RShoulder],
        [Joint.RShoulder, Joint.RElbow],
        [Joint.RElbow, Joint.RWrist],
        [Joint.RShoulder, Joint.REar],

        [Joint.Neck, Joint.LShoulder],
        [Joint.LShoulder, Joint.LElbow],
        [Joint.LElbow, Joint.LWrist],
        [Joint.LShoulder, Joint.LEar],

        [Joint.Neck, Joint.Nose],
        [Joint.Nose, Joint.REye],
        [Joint.Nose, Joint.LEye],
        [Joint.REye, Joint.REar],
        [Joint.LEye, Joint.LEar],
    ]

    # original coco keypoint order, here we use 
    # Joint to represent it.
    coco_keypoints = [
        Joint.Nose,
        Joint.LEye,
        Joint.REye,
        Joint.LEar,
        Joint.REar,
        Joint.LShoulder,
        Joint.RShoulder,
        Joint.LElbow,
        Joint.RElbow,
        Joint.LWrist,
        Joint.RWrist,
        Joint.LHip,
        Joint.RHip,
        Joint.LKnee,
        Joint.RKnee,
        Joint.LAnkle,
        Joint.RAnkle,
    ]

    # Training Parameters
    insize = 368
    min_area = 32 * 32
    min_keypoints = 5
    heatmap_sigma = 7
    paf_sigma = 8 # aka `limb width`

    # Inference Parameters
    infer_insize = 368
    infer_scales = [0.5, 1.0, 1.5, 2.0]
    # TODO: heatmap size means what?
    heatmap_size = 320
    gaussian_sigma = 2.5
    gaussian_ksize = 17
    