# Image assets

The six square portraits in `portraits/` were generated specifically for this
HAL2030 prototype with OpenAI's built-in image generation tool on 14 November
2026. The people and mission patches are fictional. The pictures are not
photographs of real astronauts and do not imply NASA endorsement.

All six source images are 1254 × 1254 pixels and are included unchanged. The
application applies its own circular crop and status ring when drawing them.
No image generation service or internet connection is needed at runtime.

## Portraits

| File | Fictional identity | Character description |
| --- | --- | --- |
| `portraits/idan.png` | Idan | Male, short dark hair, clean shaven |
| `portraits/itay.png` | Itay | Male, dark curly hair, light stubble |
| `portraits/anton.png` | Anton | Male, short brown hair, neat beard |
| `portraits/emily.png` | Emily Carter | Female, Black American, natural hair tied back |
| `portraits/sofia.png` | Sofia Almeida | Female, Brazilian, brown hair tied back |
| `portraits/camila.png` | Camila Santos | Female, Brazilian, short dark hair |

## Generation prompt

Each portrait was generated separately using the following shared prompt with
the identity and appearance from the table substituted for `SUBJECT`:

> Use case: photorealistic-natural. Asset type: square individual portrait for
> a fictional spacecraft crew monitoring application. Create a realistic
> editorial studio portrait of SUBJECT, professional approachable expression.
> Chest up facing camera, very large clearly visible face, head centered with
> a little room above hair for circular avatar cropping. Blue NASA-style flight
> suit, restrained unlettered circular star mission patch, no visible NASA
> logo, no text, no name. Dark navy seamless studio backdrop, subtle cyan rim
> lighting and soft warm facial light, realistic skin and fabric texture,
> tasteful professional photographic look. No helmet, no gadgets, no
> watermarks. This is a fictional character, not a portrait of a real astronaut.

The HAL2030 lens and interface decorations are programmatically drawn UI
graphics rather than photographs or externally loaded assets.
