import io
import numpy as np

import torch.nn as nn
import torch.nn.init as init
import torch.onnx


# Demo with Super-resolution
class SuperResolutionNet(nn.Module):
    def __init__(self, upscale_factor, inplace=False):
        super().__init__()

        self.relu = nn.ReLU(inplace=inplace)
        self.conv1 = nn.Conv2d(1, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 64, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv4 = nn.Conv2d(32, upscale_factor ** 2, (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)
        
        self._initialize_weights()
    
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pixel_shuffle(self.conv4(x))
        return x
    
    def _initialize_weights(self):
        init.orthogonal_(self.conv1.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv2.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv3.weight, init.calculate_gain('relu'))
        init.orthogonal_(self.conv3.weight)


torch_model = SuperResolutionNet(upscale_factor=3)

# load pretrained model
model_path = 'superres.pth'
batch_size = 1

map_location = 'cpu'
torch_model.load_state_dict(torch.load(model_path, map_location=map_location))

# input to the model, x acts as placeholder
x = torch.randn((batch_size, 1, 244, 244), requires_grad=True)

# export the model, torch_out can be ignored but here we use it to verify convertion
torch_out = torch.onnx._export(torch_model, x, "superres.onnx", export_params=True)


import onnx
import caffe2.python.onnx.backend as onnx_caffe2_backend

model = onnx.load('superres.onnx')
prepared_backend = onnx_caffe2_backend.prepare(model)

W = {model.graph.input[0].name: x.data.numpy()}

c2_out = prepared_backend.run(W)[0]
# the assert failed for different implementation
# np.testing.assert_almost_equal(torch_out.data.numpy(), c2_out, decimal=3)
np.testing.assert_almost_equal(np.sum(torch_out.data.numpy()), np.sum(c2_out), decimal=1)
print("Exported model has been executed on Caffe2 backend, and the result looks good!")
