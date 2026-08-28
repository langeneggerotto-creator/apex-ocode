import cv2
import numpy as np
import math
from dataclasses import dataclass, asdict

W, H, FPS = 960, 540, 30


@dataclass
class SubjectState:
    x: float = 0.5
    y: float = 0.68
    scale: float = 1.0
    phase: float = 0.0
    direction: int = 1
    wardrobe_id: str = 'canonical_black'
    footwear_id: str = 'canonical_black_heels'
    identity_id: str = 'SUBJECT_A'


@dataclass
class BoundaryContract:
    name: str
    archetype: str
    duration: float = 0.7
    min_coverage: float = 0.95
    subject_scale_tolerance: float = 0.02
    screen_x_tolerance: float = 0.02
    motion_phase_tolerance: float = 0.08
    preserve_identity: bool = True
    preserve_wardrobe: bool = True
    preserve_footwear: bool = True
    preserve_camera_axis: bool = True
    allow_world_change: bool = True
    audio_master_continuous: bool = True


PALETTES = {
    'warm_room': ((45, 28, 18), (120, 75, 35), (210, 170, 90)),
    'green_corridor': ((16, 34, 29), (34, 75, 62), (170, 145, 90)),
    'red_stage': ((28, 10, 18), (88, 18, 28), (230, 82, 55)),
    'blue_ocean': ((10, 42, 70), (18, 98, 145), (170, 225, 240)),
    'rope_room': ((22, 20, 18), (60, 50, 38), (155, 120, 78)),
    'crimson_stage': ((38, 8, 14), (128, 20, 28), (245, 88, 45)),
    'pool_room': ((12, 25, 22), (20, 58, 48), (175, 160, 95)),
}


def lerp(a, b, t):
    return a * (1 - t) + b * t


def draw_env(name, cam_dx=0.0):
    c0, c1, c2 = PALETTES[name]
    y = np.linspace(0, 1, H)[:, None, None]
    base = np.array(c0)[None, None, :] * (1 - y) + np.array(c1)[None, None, :] * y
    img = np.tile(base, (1, W, 1)).astype(np.uint8)
    cx = int(W * (0.5 + cam_dx))
    for k in range(1, 7):
        frac = k / 7
        xoff = int((W * 0.48) * (1 - frac))
        yy = int(H * (0.15 + 0.8 * frac))
        cv2.line(img, (cx - xoff, yy), (cx - int(xoff * 0.82), H), c2, 2)
        cv2.line(img, (cx + xoff, yy), (cx + int(xoff * 0.82), H), c2, 2)
    for i in range(8):
        yy = int(H * (0.55 + i * 0.055))
        cv2.line(img, (0, yy), (W, yy), tuple(int(v * 0.55) for v in c2), 1)
    for x in (0.16, 0.84):
        cv2.circle(img, (int(W * x), int(H * 0.24)), 18, c2, -1)
        cv2.circle(img, (int(W * x), int(H * 0.24)), 36, tuple(int(v * 0.45) for v in c2), 3)
    return img


def draw_subject(img, state: SubjectState, color=(28, 28, 30)):
    s = state.scale
    cx = int(W * state.x)
    foot_y = int(H * state.y)
    bob = int(4 * math.sin(state.phase * 2 * math.pi))
    head_r = int(22 * s)
    torso_h = int(120 * s)
    torso_w = int(54 * s)
    head = (cx, foot_y - int(210 * s) + bob)
    cv2.ellipse(img, (head[0], head[1] - 2), (head_r + 7, int(head_r * 1.3)), 0, 0, 360, (38, 25, 18), -1)
    cv2.circle(img, head, head_r, (210, 185, 165), -1)
    top_y = head[1] + head_r
    pts = np.array([
        [cx - int(torso_w * .38), top_y],
        [cx + int(torso_w * .38), top_y],
        [cx + int(torso_w * .75), top_y + torso_h],
        [cx - int(torso_w * .75), top_y + torso_h],
    ], np.int32)
    cv2.fillConvexPoly(img, pts, color)
    p = math.sin(state.phase * 2 * math.pi)
    hip_y = top_y + torso_h
    leg_len = int(72 * s)
    dx = int(18 * s * p * state.direction)
    for sign in (-1, 1):
        x0 = cx + int(sign * 13 * s)
        x1 = x0 + dx * sign
        cv2.line(img, (x0, hip_y), (x1, hip_y + leg_len), (205, 180, 160), int(9 * s))
        cv2.line(img, (x1 - 5, hip_y + leg_len), (x1 + 12, hip_y + leg_len), (18, 18, 20), int(6 * s))
        cv2.line(img, (x1 + 8, hip_y + leg_len), (x1 + 8, hip_y + leg_len + int(10 * s)), (18, 18, 20), int(3 * s))
    arm_phase = math.sin(state.phase * 2 * math.pi + math.pi)
    for sign in (-1, 1):
        x0 = cx + int(sign * torso_w * .4)
        y0 = top_y + int(26 * s)
        x1 = x0 + int(sign * 20 * s + arm_phase * 10 * s)
        y1 = y0 + int(82 * s)
        cv2.line(img, (x0, y0), (x1, y1), (205, 180, 160), int(7 * s))
    return img


def render_scene(env, state, cam_dx=0.0):
    return draw_subject(draw_env(env, cam_dx), state)


def alpha_comp(a, b, mask):
    m = mask[..., None].astype(np.float32)
    return np.clip(a * (1 - m) + b * m, 0, 255).astype(np.uint8)


def soft_rect_mask(x0, y0, x1, y1, feather=8):
    mask = np.zeros((H, W), np.float32)
    cv2.rectangle(mask, (int(x0), int(y0)), (int(x1), int(y1)), 1, -1)
    if feather:
        k = feather * 2 + 1
        mask = cv2.GaussianBlur(mask, (k, k), 0)
    return np.clip(mask, 0, 1)


def coverage(mask):
    return float(np.mean(mask > 0.5))


def transition_portal(src_env, tgt_env, frames, state):
    out, cov = [], []
    src = render_scene(src_env, state)
    for i in range(frames):
        t = i / max(frames - 1, 1)
        ease = 3 * t * t - 2 * t * t * t
        target = render_scene(tgt_env, state)
        ww = lerp(W * .25, W * 1.08, ease)
        hh = lerp(H * .35, H * 1.08, ease)
        x0, x1 = W / 2 - ww / 2, W / 2 + ww / 2
        y0, y1 = H / 2 - hh / 2, H / 2 + hh / 2
        m = soft_rect_mask(max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1), 6)
        fr = alpha_comp(src, target, m)
        if ww < W * 1.02:
            cv2.rectangle(fr, (int(max(0, x0)), int(max(0, y0))), (int(min(W - 1, x1)), int(min(H - 1, y1))), (190, 150, 85), 6)
        out.append(fr)
        cov.append(coverage(m))
    return out, cov


def transition_threshold(src_env, tgt_env, frames, state):
    out, cov = [], []
    for i in range(frames):
        t = i / max(frames - 1, 1)
        ease = 3 * t * t - 2 * t * t * t
        source = render_scene(src_env, state, cam_dx=-.12 * ease)
        target = render_scene(tgt_env, state, cam_dx=.02)
        ww = lerp(W * .18, W * 1.05, ease)
        hh = lerp(H * .65, H * 1.05, ease)
        x0, x1 = W * .62 - ww / 2, W * .62 + ww / 2
        y0, y1 = H * .5 - hh / 2, H * .5 + hh / 2
        m = soft_rect_mask(max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1), 4)
        out.append(alpha_comp(source, target, m))
        cov.append(coverage(m))
    return out, cov


def transition_full_wipe(src_env, tgt_env, frames, state, kind='curtain'):
    out, cov = [], []
    switch = frames // 2
    for i in range(frames):
        t = i / max(frames - 1, 1)
        base = render_scene(src_env if i < switch else tgt_env, state)
        mask = np.zeros((H, W), np.float32)
        if t <= .5:
            p = t / .5
            mask[:, int(W * (1 - p)):] = 1
        else:
            p = (t - .5) / .5
            mask[:, int(W * p):] = 1
        col = (44, 28, 92) if kind == 'curtain' else (18, 18, 18)
        occ = np.zeros_like(base)
        occ[:] = col
        if kind == 'clapper':
            for x in range(-W, W, 90):
                cv2.line(occ, (x, 0), (x + 120, H), (220, 220, 220), 18)
        out.append(alpha_comp(base, occ, mask))
        cov.append(coverage(mask))
    return out, cov


def transition_graphic_match(src_env, tgt_env, frames, state):
    out, cov = [], []
    switch = frames // 2
    for i in range(frames):
        t = i / max(frames - 1, 1)
        base = render_scene(src_env if i < switch else tgt_env, state)
        mask = np.zeros((H, W), np.uint8)
        if t < .5:
            p = t / .5
            level = int(H * (1 - p))
            cv2.rectangle(mask, (0, level), (W, H), 255, -1)
            for k in range(16):
                ang = 2 * math.pi * k / 16
                r = lerp(20, 320, p)
                x = int(W / 2 + math.cos(ang) * r * .65)
                y = int(H / 2 + math.sin(ang) * r * .42)
                cv2.circle(mask, (x, y), int(lerp(24, 135, p)), 255, -1)
        else:
            p = (t - .5) / .5
            cv2.rectangle(mask, (0, 0), (W, H), 255, -1)
            hole = int(lerp(0, 185, p))
            if hole:
                cv2.circle(mask, (W // 2, H // 2), hole, 0, -1)
        m = cv2.GaussianBlur(mask, (31, 31), 0).astype(np.float32) / 255
        occ = np.zeros_like(base)
        occ[:] = (180, 120, 40)
        fr = alpha_comp(base, occ, m)
        if t > .45:
            r = int(lerp(220, 130, min(1, (t - .45) / .55)))
            cv2.circle(fr, (W // 2, H // 2), r, (235, 235, 225), 28)
            for a in (45, 135, 225, 315):
                rad = math.radians(a)
                x1, y1 = int(W / 2 + math.cos(rad) * (r - 15)), int(H / 2 + math.sin(rad) * (r - 15))
                x2, y2 = int(W / 2 + math.cos(rad) * (r + 15)), int(H / 2 + math.sin(rad) * (r + 15))
                cv2.line(fr, (x1, y1), (x2, y2), (45, 115, 155), 28)
        out.append(fr)
        cov.append(coverage(m))
    return out, cov


def transition_material_morph(src_env, tgt_env, frames, state):
    out, cov = [], []
    switch = frames // 2
    rng = np.random.default_rng(7)
    particles = [(rng.uniform(0, W), rng.uniform(H * .45, H), rng.uniform(15, 48)) for _ in range(80)]
    for i in range(frames):
        t = i / max(frames - 1, 1)
        base = render_scene(src_env if i < switch else tgt_env, state)
        p = t / .5 if t <= .5 else (1 - t) / .5
        mask = np.zeros((H, W), np.uint8)
        level = int(H * (1 - min(1, p * 1.15)))
        cv2.rectangle(mask, (0, level), (W, H), 255, -1)
        for x, y, r in particles:
            yy = y - p * H * .75
            cv2.circle(mask, (int(x), int(yy)), int(r * (.6 + p)), 255, -1)
        m = cv2.GaussianBlur(mask, (31, 31), 0).astype(np.float32) / 255
        occ = np.zeros_like(base)
        occ[:] = (36, 48, 190) if i < switch else (26, 34, 215)
        for k in range(70):
            x = int((k * 47 + i * 18) % W)
            y = int((k * 31 + i * 25) % H)
            cv2.line(occ, (x, y), (x + 50, y - 35), (90, 130, 250), 8)
        out.append(alpha_comp(base, occ, m))
        cov.append(coverage(m))
    return out, cov


def transition_whip_flash(src_env, tgt_env, frames, state):
    out, cov = [], []
    switch = frames // 2
    for i in range(frames):
        t = i / max(frames - 1, 1)
        p = 1 - abs(2 * t - 1)
        env = src_env if i < switch else tgt_env
        fr = render_scene(env, state, cam_dx=.18 * (t - .5))
        k = int(1 + 2 * int(lerp(1, 17, p)))
        if k % 2 == 0:
            k += 1
        fr = cv2.GaussianBlur(fr, (k, 1), 0)
        fr = cv2.addWeighted(fr, 1 - .35 * p, np.full_like(fr, 255), .35 * p, 0)
        out.append(fr)
        cov.append(float(p))
    return out, cov


def transition_match_action(src_env, tgt_env, frames, state):
    out, cov = [], []
    switch = frames // 2
    for i in range(frames):
        st = SubjectState(**{**asdict(state), 'phase': (state.phase + i / (frames * 2)) % 1})
        out.append(render_scene(src_env if i < switch else tgt_env, st))
        cov.append(0.0)
    return out, cov


def frame_mae(a, b):
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga - gb)))


def verify_transition(frames, covs, contract: BoundaryContract, state_a: SubjectState, state_b: SubjectState):
    diffs = [frame_mae(frames[i - 1], frames[i]) for i in range(1, len(frames))]
    peak = max(diffs) if diffs else 0.0
    med = float(np.median(diffs)) if diffs else 0.0
    max_cov = max(covs) if covs else 0.0
    scale_err = abs(state_a.scale - state_b.scale)
    x_err = abs(state_a.x - state_b.x)
    phase_err = min(abs(state_a.phase - state_b.phase), 1 - abs(state_a.phase - state_b.phase))
    identity_ok = (not contract.preserve_identity) or state_a.identity_id == state_b.identity_id
    wardrobe_ok = (not contract.preserve_wardrobe) or state_a.wardrobe_id == state_b.wardrobe_id
    footwear_ok = (not contract.preserve_footwear) or state_a.footwear_id == state_b.footwear_id
    conceal = contract.archetype in {'curtain_wipe', 'clapperboard_wipe', 'feather_material_wipe', 'water_graphic_match', 'whip_flash'}
    coverage_score = 1.0 if not conceal else min(1, max_cov / max(contract.min_coverage, 1e-6))
    continuity_score = max(0, 1 - scale_err / max(contract.subject_scale_tolerance, 1e-6)) * .18
    continuity_score += max(0, 1 - x_err / max(contract.screen_x_tolerance, 1e-6)) * .12
    continuity_score += max(0, 1 - phase_err / max(contract.motion_phase_tolerance, 1e-6)) * .10
    invariant_score = (identity_ok + wardrobe_ok + footwear_ok) / 3 * .25
    masking_score = coverage_score * .20
    smoothness = max(0, 1 - min(1, peak / 80)) * .15
    total = (continuity_score + invariant_score + masking_score + smoothness) * 100
    passed = total >= 90 and identity_ok and wardrobe_ok and footwear_ok
    passed = passed and scale_err <= contract.subject_scale_tolerance
    passed = passed and x_err <= contract.screen_x_tolerance
    passed = passed and phase_err <= contract.motion_phase_tolerance
    passed = passed and coverage_score >= .98
    return {
        'name': contract.name,
        'archetype': contract.archetype,
        'score': round(total, 2),
        'max_coverage': round(max_cov, 3),
        'peak_frame_mae': round(peak, 3),
        'median_frame_mae': round(med, 3),
        'subject_scale_error': round(scale_err, 4),
        'screen_x_error': round(x_err, 4),
        'motion_phase_error': round(phase_err, 4),
        'identity_ok': bool(identity_ok),
        'wardrobe_ok': bool(wardrobe_ok),
        'footwear_ok': bool(footwear_ok),
        'pass': bool(passed),
    }


TRANSITION_FUNCS = {
    'nested_portal': transition_portal,
    'threshold_move': transition_threshold,
    'curtain_wipe': lambda a, b, n, s: transition_full_wipe(a, b, n, s, 'curtain'),
    'clapperboard_wipe': lambda a, b, n, s: transition_full_wipe(a, b, n, s, 'clapper'),
    'feather_material_wipe': transition_material_morph,
    'water_graphic_match': transition_graphic_match,
    'whip_flash': transition_whip_flash,
    'match_on_action': transition_match_action,
}
