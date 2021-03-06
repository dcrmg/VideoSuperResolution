#  Copyright (c): Wenyi Tang 2017-2019.
#  Author: Wenyi Tang
#  Email: wenyi.tang@intel.com
#  Update Date: 2019 - 3 - 15

import torch
import torch.nn.functional as F

from .Model import SuperResolution
from .edsr import edsr, mdsr
from ..Util import Metrics
from VSR.Util.Config import Config


class EDSR(SuperResolution):

  def __init__(self, scale, **kwargs):
    super(EDSR, self).__init__(scale, 3)
    args = Config(kwargs)
    args.scale = [scale]
    self.rgb_range = args.rgb_range
    self.edsr = edsr.EDSR(args)
    self.opt = torch.optim.Adam(self.trainable_variables(), 1e-4)

  def train(self, inputs, labels, learning_rate=None):
    sr = self.edsr(inputs[0] * self.rgb_range) / self.rgb_range
    loss = F.l1_loss(sr, labels[0])
    if learning_rate:
      for param_group in self.opt.param_groups:
        param_group["lr"] = learning_rate
    self.opt.zero_grad()
    loss.backward()
    self.opt.step()
    return {'l1': loss.detach().cpu().numpy()}

  def eval(self, inputs, labels=None, **kwargs):
    metrics = {}
    sr = self.edsr(inputs[0] * self.rgb_range) / self.rgb_range
    sr = sr.cpu().detach()
    if labels is not None:
      metrics['psnr'] = Metrics.psnr(sr.numpy(), labels[0].cpu().numpy())
    return [sr.numpy()], metrics


class MSDR(SuperResolution):

  def __init__(self, scale, **kwargs):
    super(MSDR, self).__init__(scale, 3)
    args = Config(kwargs)
    args.scale = [2, 3, 4]
    self.scales = args.scale
    self.rgb_range = args.rgb_range
    self.edsr = mdsr.MDSR(args)
    self.opt = torch.optim.Adam(self.trainable_variables(), 1e-4)

  def train(self, inputs, labels, learning_rate=None):
    # TODO
    self.edsr.set_scale(2)
    sr = self.edsr(inputs[0] * self.rgb_range) / self.rgb_range
    loss = F.l1_loss(sr, labels[0])
    if learning_rate:
      for param_group in self.opt.param_groups:
        param_group["lr"] = learning_rate
    self.opt.zero_grad()
    loss.backward()
    self.opt.step()
    return {'l1': loss.detach().cpu().numpy()}

  def eval(self, inputs, labels=None, **kwargs):
    metrics = {}
    self.edsr.set_scale(self.scales.index(self.scale))
    sr = self.edsr(inputs[0] * self.rgb_range) / self.rgb_range
    sr = sr.cpu().detach()
    if labels is not None:
      metrics['psnr'] = Metrics.psnr(sr.numpy(), labels[0].cpu().numpy())
    return [sr.numpy()], metrics
