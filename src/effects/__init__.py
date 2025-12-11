from ..core.effects import EffectRegistry
from .adjustments import InvertEffect, BrightnessContrastEffect, HueSaturationEffect, AutoLevelEffect
from .blurs import GaussianBlurEffect, SharpenEffect, MotionBlurEffect, SepiaEffect, MedianEffect
from .distort import (PixelateEffect, EmbossEffect, EdgeDetectEffect, 
                      AddNoiseEffect, ReduceNoiseEffect, RadialBlurEffect,
                      ZoomBlurEffect, BulgeEffect, TwistEffect, DentsEffect)
from .photo import (CurvesEffect, LevelsEffect, VignetteEffect, 
                    OilPaintingEffect, PosterizeEffect, BlackWhiteEffect,
                    RedEyeRemovalEffect, SurfaceBlurEffect)
from .render import (GlowEffect, OutlineEffect, FragmentEffect, 
                     CloudsEffect, TileReflectionEffect)
from .artistic import PencilSketchEffect, InkSketchEffect, CrystallizeEffect

def register_all_effects():
    # Adjustments
    EffectRegistry.register(InvertEffect)
    EffectRegistry.register(BrightnessContrastEffect)
    EffectRegistry.register(HueSaturationEffect)
    EffectRegistry.register(AutoLevelEffect)
    EffectRegistry.register(SepiaEffect)
    EffectRegistry.register(CurvesEffect)
    EffectRegistry.register(LevelsEffect)
    EffectRegistry.register(PosterizeEffect)
    EffectRegistry.register(BlackWhiteEffect)
    
    # Blurs
    EffectRegistry.register(GaussianBlurEffect)
    EffectRegistry.register(SharpenEffect)
    EffectRegistry.register(MotionBlurEffect)
    EffectRegistry.register(RadialBlurEffect)
    EffectRegistry.register(ZoomBlurEffect)
    EffectRegistry.register(SurfaceBlurEffect)
    EffectRegistry.register(MedianEffect)
    
    # Distort
    EffectRegistry.register(PixelateEffect)
    EffectRegistry.register(BulgeEffect)
    EffectRegistry.register(TwistEffect)
    EffectRegistry.register(TileReflectionEffect)
    EffectRegistry.register(DentsEffect)
    
    # Stylize
    EffectRegistry.register(EmbossEffect)
    EffectRegistry.register(EdgeDetectEffect)
    EffectRegistry.register(OutlineEffect)
    EffectRegistry.register(FragmentEffect)
    
    # Noise
    EffectRegistry.register(AddNoiseEffect)
    EffectRegistry.register(ReduceNoiseEffect)
    
    # Photo
    EffectRegistry.register(VignetteEffect)
    EffectRegistry.register(GlowEffect)
    EffectRegistry.register(RedEyeRemovalEffect)
    
    # Artistic
    EffectRegistry.register(OilPaintingEffect)
    EffectRegistry.register(PencilSketchEffect)
    EffectRegistry.register(InkSketchEffect)
    EffectRegistry.register(CrystallizeEffect)
    
    # Render
    EffectRegistry.register(CloudsEffect)
