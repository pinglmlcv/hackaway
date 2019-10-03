#
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import numpy as np



# here start STN（GMM）
class FeatureExtraction(nn.Module):
    """Feature Extraction Layer, the first part of GMM, extract features
    from cloth c and person representation"""
    def __init__(self, in_channels):
        super().__init__()
        self.conv1 = nn.Sequential(
                nn.Conv2d(in_channels, 16, 3, 1, 1),
                nn.ReLU(True),
                nn.BatchNorm2d(16),
                nn.Conv2d(16, 16, 3, 2, 1),
            )
        self.conv2 = nn.Sequential(
                nn.Conv2d(16, 32, 3, 1, 1),
                nn.ReLU(True),
                nn.BatchNorm2d(32),
                nn.Conv2d(32, 32, 3, 2, 1),
            )
        self.conv3 = nn.Sequential(
                nn.Conv2d(32, 64, 3, 1, 1),
                nn.ReLU(True),
                nn.BatchNorm2d(64),
                nn.Conv2d(64, 64, 3, 2, 1),
            )
        self.conv4 = nn.Sequential(
                nn.Conv2d(64, 128, 3, 1, 1),
                nn.ReLU(True),
                nn.BatchNorm2d(128),
                nn.Conv2d(128, 128, 3, 2, 1),
            )
        self.conv5 = nn.Sequential(
                nn.Conv2d(128, 256, 3, 1, 1),
                nn.ReLU(True),
                nn.BatchNorm2d(256),
                nn.Conv2d(256, 256, 3, 2, 1),
            )

    def forward(self, x):
        o1 = self.conv1(x)
        o2 = self.conv2(o1)
        o3 = self.conv3(o2)
        o4 = self.conv4(o3)
        o5 = self.conv5(o4)
        return [o1, o2, o3, o4, o5]



# mory NOTE: 特征规范化论文中似乎没有提及，可能是进行融合p和c的特征之前所做的预处理过程
class FeatureL2Norm(nn.Module):
    def __init__(self):
        super(FeatureL2Norm, self).__init__()

    def forward(self, feature):
        epsilon = 1e-6
        norm = torch.pow(torch.sum(torch.pow(feature,2),1)+epsilon,0.5).unsqueeze(1).expand_as(feature)
        return torch.div(feature,norm)


# mory NOTE: 将不同的特征在不同的channel上进行融合
class FeatureCorrelation(nn.Module):
    def __init__(self):
        super(FeatureCorrelation, self).__init__()

    def forward(self, feature_A, feature_B):
        b,c,h,w = feature_A.size()
        # reshape features for matrix multiplication
        feature_A = feature_A.transpose(2,3).contiguous().view(b,c,h*w)
        feature_B = feature_B.view(b,c,h*w).transpose(1,2)
        # perform matrix mult.
        feature_mul = torch.bmm(feature_B,feature_A)
        correlation_tensor = feature_mul.view(b,h,w,h*w).transpose(2,3).transpose(1,2)
        return correlation_tensor

# mory NOTE: 论文中写Regression Network的输出应该是50个点，这里默认输出6个点
class FeatureRegression(nn.Module):
    def __init__(self, input_nc=512, output_dim=6, use_cuda=True):
        super(FeatureRegression, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(input_nc, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        self.linear = nn.Linear(128, output_dim)
        self.tanh = nn.Tanh()
        if use_cuda:
            self.conv.cuda()
            self.linear.cuda()
            self.tanh.cuda()

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.linear(x)
        x = self.tanh(x)
        return x



# TPS transform
# Refer to original paper for detail explaintation.
class TpsGridGen(nn.Module):
    def __init__(self, out_h=256, out_w=192, use_regular_grid=True, grid_size=3, reg_factor=0, use_cuda=True):
        super(TpsGridGen, self).__init__()
        self.out_h, self.out_w = out_h, out_w
        self.reg_factor = reg_factor
        self.use_cuda = use_cuda

        # create grid in numpy
        self.grid = np.zeros( [self.out_h, self.out_w, 3], dtype=np.float32)
        # sampling grid with dim-0 coords (Y)
        self.grid_X,self.grid_Y = np.meshgrid(np.linspace(-1,1,out_w),np.linspace(-1,1,out_h))
        # grid_X,grid_Y: size [1,H,W,1,1]
        self.grid_X = torch.FloatTensor(self.grid_X).unsqueeze(0).unsqueeze(3)
        self.grid_Y = torch.FloatTensor(self.grid_Y).unsqueeze(0).unsqueeze(3)
        if use_cuda:
            self.grid_X = self.grid_X.cuda()
            self.grid_Y = self.grid_Y.cuda()

        # initialize regular grid for control points P_i
        if use_regular_grid:
            axis_coords = np.linspace(-1,1,grid_size)
            self.N = grid_size*grid_size
            P_Y,P_X = np.meshgrid(axis_coords,axis_coords)
            P_X = np.reshape(P_X,(-1,1)) # size (N,1)
            P_Y = np.reshape(P_Y,(-1,1)) # size (N,1)
            P_X = torch.FloatTensor(P_X)
            P_Y = torch.FloatTensor(P_Y)
            self.P_X_base = P_X.clone()
            self.P_Y_base = P_Y.clone()
            self.Li = self.compute_L_inverse(P_X,P_Y).unsqueeze(0)
            self.P_X = P_X.unsqueeze(2).unsqueeze(3).unsqueeze(4).transpose(0,4)
            self.P_Y = P_Y.unsqueeze(2).unsqueeze(3).unsqueeze(4).transpose(0,4)
            if use_cuda:
                self.P_X = self.P_X.cuda()
                self.P_Y = self.P_Y.cuda()
                self.P_X_base = self.P_X_base.cuda()
                self.P_Y_base = self.P_Y_base.cuda()


    def forward(self, theta):
        warped_grid = self.apply_transformation(theta,torch.cat((self.grid_X,self.grid_Y),3))

        return warped_grid

    def compute_L_inverse(self,X,Y):
        N = X.size()[0] # num of points (along dim 0)
        # construct matrix K
        Xmat = X.expand(N,N)
        Ymat = Y.expand(N,N)
        P_dist_squared = torch.pow(Xmat-Xmat.transpose(0,1),2)+torch.pow(Ymat-Ymat.transpose(0,1),2)
        P_dist_squared[P_dist_squared==0]=1 # make diagonal 1 to avoid NaN in log computation
        K = torch.mul(P_dist_squared,torch.log(P_dist_squared))
        # construct matrix L
        O = torch.FloatTensor(N,1).fill_(1)
        Z = torch.FloatTensor(3,3).fill_(0)
        P = torch.cat((O,X,Y),1)
        L = torch.cat((torch.cat((K,P),1),torch.cat((P.transpose(0,1),Z),1)),0)
        Li = torch.inverse(L)
        if self.use_cuda:
            Li = Li.cuda()
        return Li

    def apply_transformation(self,theta,points):
        if theta.dim()==2:
            theta = theta.unsqueeze(2).unsqueeze(3)
        # points should be in the [B,H,W,2] format,
        # where points[:,:,:,0] are the X coords
        # and points[:,:,:,1] are the Y coords

        # input are the corresponding control points P_i
        batch_size = theta.size()[0]
        # split theta into point coordinates
        Q_X=theta[:,:self.N,:,:].squeeze(3)
        Q_Y=theta[:,self.N:,:,:].squeeze(3)
        Q_X = Q_X + self.P_X_base.expand_as(Q_X)
        Q_Y = Q_Y + self.P_Y_base.expand_as(Q_Y)

        # get spatial dimensions of points
        points_b = points.size()[0]
        points_h = points.size()[1]
        points_w = points.size()[2]

        # repeat pre-defined control points along spatial dimensions of points to be transformed
        P_X = self.P_X.expand((1,points_h,points_w,1,self.N))
        P_Y = self.P_Y.expand((1,points_h,points_w,1,self.N))

        # compute weigths for non-linear part
        W_X = torch.bmm(self.Li[:,:self.N,:self.N].expand((batch_size,self.N,self.N)),Q_X)
        W_Y = torch.bmm(self.Li[:,:self.N,:self.N].expand((batch_size,self.N,self.N)),Q_Y)
        # reshape
        # W_X,W,Y: size [B,H,W,1,N]
        W_X = W_X.unsqueeze(3).unsqueeze(4).transpose(1,4).repeat(1,points_h,points_w,1,1)
        W_Y = W_Y.unsqueeze(3).unsqueeze(4).transpose(1,4).repeat(1,points_h,points_w,1,1)
        # compute weights for affine part
        A_X = torch.bmm(self.Li[:,self.N:,:self.N].expand((batch_size,3,self.N)),Q_X)
        A_Y = torch.bmm(self.Li[:,self.N:,:self.N].expand((batch_size,3,self.N)),Q_Y)
        # reshape
        # A_X,A,Y: size [B,H,W,1,3]
        A_X = A_X.unsqueeze(3).unsqueeze(4).transpose(1,4).repeat(1,points_h,points_w,1,1)
        A_Y = A_Y.unsqueeze(3).unsqueeze(4).transpose(1,4).repeat(1,points_h,points_w,1,1)

        # compute distance P_i - (grid_X,grid_Y)
        # grid is expanded in point dim 4, but not in batch dim 0, as points P_X,P_Y are fixed for all batch
        points_X_for_summation = points[:,:,:,0].unsqueeze(3).unsqueeze(4).expand(points[:,:,:,0].size()+(1,self.N))
        points_Y_for_summation = points[:,:,:,1].unsqueeze(3).unsqueeze(4).expand(points[:,:,:,1].size()+(1,self.N))

        if points_b==1:
            delta_X = points_X_for_summation-P_X
            delta_Y = points_Y_for_summation-P_Y
        else:
            # use expanded P_X,P_Y in batch dimension
            delta_X = points_X_for_summation-P_X.expand_as(points_X_for_summation)
            delta_Y = points_Y_for_summation-P_Y.expand_as(points_Y_for_summation)

        dist_squared = torch.pow(delta_X,2)+torch.pow(delta_Y,2)
        # U: size [1,H,W,1,N]
        dist_squared[dist_squared==0]=1 # avoid NaN in log computation
        U = torch.mul(dist_squared,torch.log(dist_squared))

        # expand grid in batch dimension if necessary
        points_X_batch = points[:,:,:,0].unsqueeze(3)
        points_Y_batch = points[:,:,:,1].unsqueeze(3)
        if points_b==1:
            points_X_batch = points_X_batch.expand((batch_size,)+points_X_batch.size()[1:])
            points_Y_batch = points_Y_batch.expand((batch_size,)+points_Y_batch.size()[1:])

        points_X_prime = A_X[:,:,:,:,0]+ \
                       torch.mul(A_X[:,:,:,:,1],points_X_batch) + \
                       torch.mul(A_X[:,:,:,:,2],points_Y_batch) + \
                       torch.sum(torch.mul(W_X,U.expand_as(W_X)),4)

        points_Y_prime = A_Y[:,:,:,:,0]+ \
                       torch.mul(A_Y[:,:,:,:,1],points_X_batch) + \
                       torch.mul(A_Y[:,:,:,:,2],points_Y_batch) + \
                       torch.sum(torch.mul(W_Y,U.expand_as(W_Y)),4)

        return torch.cat((points_X_prime,points_Y_prime),3)


class GMM(nn.Module):
    """ Geometric Matching Module
    """
    def __init__(self, fine_height, fine_width, grid_size):
        super(GMM, self).__init__()
        self.extractionA = FeatureExtraction(3)
        self.extractionB = FeatureExtraction(3)
        self.l2norm = FeatureL2Norm()
        self.correlation = FeatureCorrelation()
        self.regression = FeatureRegression(input_nc=48, output_dim=2*grid_size**2, use_cuda=False)

    def forward(self, inputA, inputB):
        featureA = self.extractionA(inputA)
        featureB = self.extractionB(inputB)
        featureA = self.l2norm(featureA[-1])
        featureB = self.l2norm(featureB[-1])
        correlation = self.correlation(featureA, featureB)
        theta = self.regression(correlation)
        return theta

class DNet(nn.Module):
    def __init__(self, fine_height, fine_width):
        super().__init__()
        self.deconv1 = nn.Sequential(
            nn.Conv2d(512, 256, 3, 1, 1),
            nn.InstanceNorm2d(256),
            nn.LeakyReLU(0.01),
        )
        self.deconv2 = nn.Sequential(
            nn.Conv2d(512, 128, 3, 1, 1),
            nn.InstanceNorm2d(128),
            nn.LeakyReLU(0.01),
        )
        self.deconv3 = nn.Sequential(
            nn.Conv2d(256, 64, 3, 1, 1),
            nn.InstanceNorm2d(64),
            nn.LeakyReLU(0.01),
        )
        self.deconv4 = nn.Sequential(
            nn.Conv2d(128, 32, 3, 1, 1),
            nn.InstanceNorm2d(32),
            nn.LeakyReLU(0.01),
        )
        self.deconv5 = nn.Sequential(
            nn.Conv2d(64, 16, 3, 1, 1),
            nn.InstanceNorm2d(16),
            nn.LeakyReLU(0.01),
        )
        self.deconv6 = nn.Conv2d(16, 3, 3, 1, 1)

    def forward(self, co, po):
        co1, co2, co3, co4, co5 = co
        po1, po2, po3, po4, po5 = po
        
        print(co5.shape, po5.shape)
        map1 = torch.cat([co5, po5], 1)
        out1 = self.deconv1(map1)
        up1 = F.interpolate(out1, scale_factor=2, mode='bilinear')

        map2 = torch.cat([co4, po4, up1], 1)
        out2 = self.deconv2(map2)
        up2 = F.interpolate(out2, scale_factor=2, mode='bilinear')

        map3 = torch.cat([co3, po3, up2], 1)
        out3 = self.deconv3(map3)
        up3 = F.interpolate(out3, scale_factor=2, mode='bilinear')

        map4 = torch.cat([co2, po2, up3], 1)
        out4 = self.deconv4(map4)
        up4 = F.interpolate(out4, scale_factor=2, mode='bilinear')

        map5 = torch.cat([co1, po1, up4], 1)
        out5 = self.deconv5(map5)
        up5 = F.interpolate(out5, scale_factor=2, mode='bilinear')

        out6 = self.deconv6(up5)
        return out6



class SiameseUnetGenerator(nn.Module):
    def __init__(self, fine_height, fine_width, grid_size):
        super().__init__()
        self.cnet = FeatureExtraction(3)
        self.pnet = FeatureExtraction(3)
        self.gmm = GMM(fine_height, fine_width, grid_size)
        self.gridGen = [
            TpsGridGen(fine_height, fine_width, use_cuda=False, grid_size=grid_size),
            TpsGridGen(fine_height//2, fine_width//2, use_cuda=False, grid_size=grid_size),
            TpsGridGen(fine_height//4, fine_width//4, use_cuda=False, grid_size=grid_size),
            TpsGridGen(fine_height//8, fine_width//8, use_cuda=False, grid_size=grid_size),
            TpsGridGen(fine_height//16, fine_width//16, use_cuda=False, grid_size=grid_size),
            TpsGridGen(fine_height//32, fine_width//32, use_cuda=False, grid_size=grid_size),
        ]
        self.dnet = DNet(fine_height, fine_width)
        
    def forward(self, cloth, person, training=True):
        co = self.cnet(cloth)
        po = self.pnet(person)
        theta = self.gmm(cloth, person)
        for i in range(len(co)):
            grid = self.gridGen[i+1](theta)
            co[i] = F.grid_sample(co[i], grid)
        warp_person = self.dnet(co, po)

        # for training
        if training:
            grid = self.gridGen[0](theta)
            warp_cloth = F.grid_sample(cloth, grid, mode='border')
        else:
            warp_cloth = None
        return warp_person, warp_cloth


# loss
class Vgg19(nn.Module):
    def __init__(self, requires_grad=False):
        super(Vgg19, self).__init__()
        vgg_pretrained_features = models.vgg19(pretrained=True).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        for x in range(2):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(2, 7):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(7, 12):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(12, 21):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(21, 30):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h_relu1 = self.slice1(X)
        h_relu2 = self.slice2(h_relu1)
        h_relu3 = self.slice3(h_relu2)
        h_relu4 = self.slice4(h_relu3)
        h_relu5 = self.slice5(h_relu4)
        out = [h_relu1, h_relu2, h_relu3, h_relu4, h_relu5]
        return out

class VGGLoss(nn.Module):
    def __init__(self, layids = None):
        super(VGGLoss, self).__init__()
        self.vgg = Vgg19()
        self.vgg.cuda()
        self.criterion = nn.L1Loss()
        self.weights = [1.0/32, 1.0/16, 1.0/8, 1.0/4, 1.0]
        self.layids = layids

    def forward(self, x, y):
        x_vgg, y_vgg = self.vgg(x), self.vgg(y)
        loss = 0
        if self.layids is None:
            self.layids = list(range(len(x_vgg)))
        for i in self.layids:
            loss += self.weights[i] * self.criterion(x_vgg[i], y_vgg[i].detach())
        return loss




if __name__ == '__main__':
    cloth = torch.randn(8, 3, 256, 192)
    mask_person  = torch.randn(8, 3, 256, 192)
    net = SiameseUnetGenerator(fine_height=256, fine_width=192, grid_size=5)
    out = net(cloth, mask_person)