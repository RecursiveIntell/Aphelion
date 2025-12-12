from ..core.effects import EffectRegistry
from .adjustments import (InvertEffect, BrightnessContrastEffect, HueSaturationEffect, 
                          AutoLevelEffect, InvertAlphaEffect, ColorBalanceEffect)
from .blurs import (GaussianBlurEffect, SharpenEffect, MotionBlurEffect, SepiaEffect, 
                    MedianEffect, UnfocusEffect)
from .distort import (PixelateEffect, EmbossEffect, EdgeDetectEffect, 
                      AddNoiseEffect, ReduceNoiseEffect, RadialBlurEffect,
                      ZoomBlurEffect, BulgeEffect, TwistEffect, DentsEffect,
                      Rotate3DEffect, PolarInversionEffect, FrostedGlassEffect)
from .photo import (CurvesEffect, LevelsEffect, VignetteEffect, 
                    OilPaintingEffect, PosterizeEffect, BlackWhiteEffect,
                    RedEyeRemovalEffect, SurfaceBlurEffect)
from .render import (GlowEffect, OutlineEffect, FragmentEffect, 
                     CloudsEffect, TileReflectionEffect, 
                     JuliaFractalEffect, MandelbrotFractalEffect)
from .artistic import PencilSketchEffect, InkSketchEffect, CrystallizeEffect
from .stylize import (DropShadowEffect, ChannelShiftEffect, 
                      BokehBlurEffect, SketchBlurEffect, ReliefEffect)

def register_all_effects():
    # Adjustments (11)
    EffectRegistry.register(InvertEffect)
    EffectRegistry.register(InvertAlphaEffect)
    EffectRegistry.register(BrightnessContrastEffect)
    EffectRegistry.register(HueSaturationEffect)
    EffectRegistry.register(AutoLevelEffect)
    EffectRegistry.register(SepiaEffect)
    EffectRegistry.register(CurvesEffect)
    EffectRegistry.register(LevelsEffect)
    EffectRegistry.register(PosterizeEffect)
    EffectRegistry.register(BlackWhiteEffect)
    EffectRegistry.register(ColorBalanceEffect)
    
    # Blurs (10)
    EffectRegistry.register(GaussianBlurEffect)
    EffectRegistry.register(SharpenEffect)
    EffectRegistry.register(MotionBlurEffect)
    EffectRegistry.register(RadialBlurEffect)
    EffectRegistry.register(ZoomBlurEffect)
    EffectRegistry.register(SurfaceBlurEffect)
    EffectRegistry.register(MedianEffect)
    EffectRegistry.register(BokehBlurEffect)
    EffectRegistry.register(SketchBlurEffect)
    EffectRegistry.register(UnfocusEffect)
    
    # Distort (9)
    EffectRegistry.register(PixelateEffect)
    EffectRegistry.register(BulgeEffect)
    EffectRegistry.register(TwistEffect)
    EffectRegistry.register(TileReflectionEffect)
    EffectRegistry.register(DentsEffect)
    EffectRegistry.register(Rotate3DEffect)
    EffectRegistry.register(PolarInversionEffect)
    EffectRegistry.register(CrystallizeEffect)
    EffectRegistry.register(FrostedGlassEffect)
    
    # Stylize (7)
    EffectRegistry.register(EmbossEffect)
    EffectRegistry.register(EdgeDetectEffect)
    EffectRegistry.register(OutlineEffect)
    EffectRegistry.register(FragmentEffect)
    EffectRegistry.register(DropShadowEffect)
    EffectRegistry.register(ChannelShiftEffect)
    EffectRegistry.register(ReliefEffect)
    
    # Noise (2)
    EffectRegistry.register(AddNoiseEffect)
    EffectRegistry.register(ReduceNoiseEffect)
    
    # Photo (3)
    EffectRegistry.register(VignetteEffect)
    EffectRegistry.register(GlowEffect)
    EffectRegistry.register(RedEyeRemovalEffect)
    
    # Artistic (4)
    EffectRegistry.register(OilPaintingEffect)
    EffectRegistry.register(PencilSketchEffect)
    EffectRegistry.register(InkSketchEffect)
    
    # Render (3)
    EffectRegistry.register(CloudsEffect)
    EffectRegistry.register(JuliaFractalEffect)
    EffectRegistry.register(MandelbrotFractalEffect)
