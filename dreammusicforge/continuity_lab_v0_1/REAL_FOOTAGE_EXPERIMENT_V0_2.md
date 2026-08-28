# APEX Continuity Lab — Real Footage Experiment v0.2

Date: 2026-08-28
Status: LOCAL REAL-FOOTAGE CONTINUITY EXPERIMENT / EVIDENCE-BOUNDED

## Objective

Apply the Continuity Lab principles to actual human video footage rather than the synthetic simulator demo.

Source footage: the three approximately 15-second woman-walking clips used in the earlier continuity experiment.

## Changes in this pass

### Door boundary

- retained the real closing/opening door motion;
- inserted a very short matched dark-door bridge rather than a long dissolve;
- matched door exposure/geometry enough to keep the handoff inside an unreadable dark surface.

### Foreground-passerby boundary

- moved the actual environment reset completely inside a full-frame fabric/passerby safe zone;
- used real passerby imagery as the bridge rather than synthetic graphics;
- avoided showing both environments simultaneously;
- used a short motion-blurred texture bridge while stable landmarks were unavailable.

### Incoming character/camera lock

The third clip was digitally reframed so the incoming woman is much closer to the outgoing clip's subject scale and screen position:

- incoming face/body scale enlarged;
- subject screen position shifted toward the outgoing state;
- scale gradually adjusted as the woman walks so the edit behaves more like a camera dolly/continuity move than a jump in distance;
- the stronger crop also reduces immediate footwear comparison at the reveal.

### Audio

The previously assembled continuous master audio was reused rather than restarting provider audio at each visual boundary.

## Output

Local artifact: `APEX_Continuity_RealFootage_v0.2.mp4`

- duration: ~44.628 s
- resolution: 512×910
- frame rate: 30 fps
- SHA-256: `594f05b59d1e73330157b1a95ae4e8f1cfdc13a9cc3314047e638ca218ef2bb7`

## Result

This pass is materially more convincing than the earlier local stitches because the second environment is no longer visible while the old environment is still available for comparison, and the incoming woman's scale/position are normalized before reveal.

However, this is still NOT proof of perfect continuity. Exact biometric identity, exact footwear geometry, exact wardrobe micro-detail and true physical world continuity were not regenerated from a common provider state. Those variables can be reduced perceptually by reframing and masking, but cannot be truthfully called identical from editing alone.

## Engineering conclusion

Real-footage editing validates the Continuity Lab architecture:

1. conceal only what is allowed to change;
2. preserve/lock what remains visible;
3. perform state resets only inside perceptual safe zones;
4. normalize subject scale and screen position before reveal;
5. maintain continuous audio independently;
6. regenerate rather than cosmetically hide any hard invariant that remains visibly incompatible.

The next provider-level experiment should use the outgoing terminal frame/state from Segment N as the explicit start/reference state for Segment N+1 so face, footwear, body scale, stride phase and camera distance are generated consistently rather than repaired after the fact.
