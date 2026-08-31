// 📌 สื่อ 3D Interactive: ระดับการจัดระบบของสิ่งมีชีวิต (โมเลกุล → เซลล์ → เนื้อเยื่อ → อวัยวะ → ระบบอวัยวะ → สิ่งมีชีวิต)
// สร้างจาก Three.js ล้วน ๆ ด้วยรูปทรงพื้นฐาน (sphere/cylinder/capsule) ไม่ต้องพึ่งไฟล์โมเดล 3D ภายนอก
// แสดงทั้ง 6 ระดับพร้อมกันเป็น "โครงสร้างเดียว" จัดเรียงเป็นเส้นทางซิกแซก แล้วกดที่ชิ้นส่วนไหนในโมเดล
// (หรือกดปุ่มด้านล่าง) จะเด้งบอกว่าส่วนนั้นคือระดับอะไร — ใช้ raycaster ของ Three.js จับการคลิกบนโมเดลจริง
// ใช้ ES modules (import three.module.min.js ที่ vendor ไว้ในเครื่อง) + OrbitControls ให้หมุน/ซูมด้วยเมาส์ได้

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const GREEN_MAIN = 0x329632;
const GREEN_DARK = 0x1f5c1f;
const GREEN_LIGHT = 0x9fd89f;
const ATOM_BLUE = 0x4a90d9;
const ATOM_RED = 0xd9534f;
const ORGAN_PINK = 0xd97a8f;

export const ORGANIZATION_LEVELS = [
    {
        key: 'molecule',
        icon: '⚛️',
        name: 'โมเลกุล (molecule)',
        desc: 'อะตอมที่สร้างพันธะกันเป็นโมเลกุล เช่น น้ำตาลที่ได้จากการสังเคราะห์ด้วยแสง เป็นหน่วยเล็กที่สุดที่ประกอบกันขึ้นเป็นสิ่งมีชีวิต',
    },
    {
        key: 'cell',
        icon: '🦠',
        name: 'เซลล์ (cell)',
        desc: 'หน่วยพื้นฐานของสิ่งมีชีวิตทุกชนิด มีเยื่อหุ้มเซลล์ห่อหุ้มของเหลวและนิวเคลียสไว้ภายใน เป็นที่เกิดกระบวนการเมแทบอลิซึมทั้งหมด',
    },
    {
        key: 'tissue',
        icon: '🧫',
        name: 'เนื้อเยื่อ (tissue)',
        desc: 'เซลล์ชนิดเดียวกันจำนวนมากมารวมตัวกันทำหน้าที่ร่วมกัน เช่น ไซเล็มและโฟลเอ็มที่ทำหน้าที่ลำเลียงสารในพืช',
    },
    {
        key: 'organ',
        icon: '🫀',
        name: 'อวัยวะ (organ)',
        desc: 'เนื้อเยื่อหลายชนิดรวมกันทำหน้าที่เฉพาะอย่าง เช่น ตับอ่อนซึ่งทำงานเกี่ยวข้องทั้งระบบย่อยอาหารและระบบต่อมไร้ท่อ',
    },
    {
        key: 'organsystem',
        icon: '🩻',
        name: 'ระบบอวัยวะ (organ system)',
        desc: 'อวัยวะหลายชิ้นทำงานประสานกันเป็นระบบ เช่น ระบบย่อยอาหารที่อวัยวะแต่ละชิ้นเชื่อมต่อกันเป็นทางเดินเดียว',
    },
    {
        key: 'organism',
        icon: '🌱',
        name: 'สิ่งมีชีวิต (organism)',
        desc: 'ระบบอวัยวะหลายระบบทำงานร่วมกันจนเป็นสิ่งมีชีวิตที่สมบูรณ์ มีลักษณะสำคัญครบทั้ง 5 ประการของสิ่งมีชีวิต',
    },
];

function makeAtom(radius, color) {
    const geo = new THREE.SphereGeometry(radius, 24, 16);
    const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.1 });
    return new THREE.Mesh(geo, mat);
}

function makeBond(from, to, color = 0xcccccc, radius = 0.05) {
    const dir = new THREE.Vector3().subVectors(to, from);
    const len = dir.length();
    const geo = new THREE.CylinderGeometry(radius, radius, len, 8);
    const mat = new THREE.MeshStandardMaterial({ color });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    return mesh;
}

function buildMolecule() {
    const group = new THREE.Group();
    const center = new THREE.Vector3(0, 0, 0);
    group.add(makeAtom(0.55, ATOM_RED).translateOnAxis(new THREE.Vector3(), 0));
    const satellites = [
        new THREE.Vector3(1.3, 0.6, 0),
        new THREE.Vector3(-1.3, 0.6, 0.4),
        new THREE.Vector3(0.3, -1.2, 0.8),
        new THREE.Vector3(-0.5, -0.9, -1.1),
        new THREE.Vector3(0.9, 0.9, -1.0),
    ];
    satellites.forEach((pos) => {
        const atom = makeAtom(0.32, ATOM_BLUE);
        atom.position.copy(pos);
        group.add(atom);
        group.add(makeBond(center, pos));
    });
    return group;
}

function buildSingleCell(radius = 1) {
    const cell = new THREE.Group();
    const membraneGeo = new THREE.SphereGeometry(radius, 32, 24);
    const membraneMat = new THREE.MeshStandardMaterial({
        color: GREEN_LIGHT, transparent: true, opacity: 0.35, roughness: 0.3,
    });
    cell.add(new THREE.Mesh(membraneGeo, membraneMat));

    const nucleus = makeAtom(radius * 0.38, GREEN_DARK);
    nucleus.position.set(radius * 0.15, radius * 0.1, radius * 0.1);
    cell.add(nucleus);

    for (let i = 0; i < 4; i++) {
        const organelle = makeAtom(radius * 0.12, GREEN_MAIN);
        const angle = (i / 4) * Math.PI * 2;
        organelle.position.set(Math.cos(angle) * radius * 0.55, Math.sin(angle) * radius * 0.4, Math.sin(angle * 1.7) * radius * 0.3);
        cell.add(organelle);
    }
    return cell;
}

function buildTissue() {
    const group = new THREE.Group();
    const positions = [
        [0, 0, 0], [1.4, 0.2, 0.3], [-1.4, -0.1, 0.2], [0.7, 1.3, -0.4],
        [-0.7, 1.2, 0.4], [0.6, -1.3, 0.3], [-0.8, -1.2, -0.3],
    ];
    positions.forEach((p) => {
        const cell = buildSingleCell(0.75);
        cell.position.set(...p);
        group.add(cell);
    });
    return group;
}

function buildOrgan() {
    const group = new THREE.Group();
    const bodyGeo = new THREE.SphereGeometry(1.6, 32, 24);
    bodyGeo.scale(1, 0.7, 0.55);
    const bodyMat = new THREE.MeshStandardMaterial({ color: ORGAN_PINK, roughness: 0.5 });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    group.add(body);

    // จุดเนื้อเยื่อบนผิวอวัยวะ (แทนว่าอวัยวะประกอบจากเนื้อเยื่อหลายชนิด)
    for (let i = 0; i < 10; i++) {
        const patch = makeAtom(0.18, i % 2 === 0 ? GREEN_MAIN : GREEN_DARK);
        const angle = (i / 10) * Math.PI * 2;
        patch.position.set(Math.cos(angle) * 1.55, Math.sin(angle * 2) * 0.45, Math.sin(angle) * 0.75);
        group.add(patch);
    }
    return group;
}

function buildOrganSystem() {
    const group = new THREE.Group();
    const organPositions = [
        new THREE.Vector3(-2.2, 1.0, 0),
        new THREE.Vector3(0, -0.6, 0.3),
        new THREE.Vector3(2.2, 1.2, -0.2),
    ];
    organPositions.forEach((pos, i) => {
        const organ = buildOrgan();
        organ.scale.setScalar(0.55);
        organ.position.copy(pos);
        group.add(organ);
        if (i > 0) {
            const tubeGeo = new THREE.CylinderGeometry(0.12, 0.12, pos.distanceTo(organPositions[i - 1]), 10);
            const tubeMat = new THREE.MeshStandardMaterial({ color: 0x8a3f4a, roughness: 0.6 });
            const tube = new THREE.Mesh(tubeGeo, tubeMat);
            tube.position.copy(pos).add(organPositions[i - 1]).multiplyScalar(0.5);
            const dir = new THREE.Vector3().subVectors(pos, organPositions[i - 1]).normalize();
            tube.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
            group.add(tube);
        }
    });
    return group;
}

function buildOrganism() {
    const group = new THREE.Group();
    const skinMat = new THREE.MeshStandardMaterial({ color: GREEN_MAIN, roughness: 0.55, transparent: true, opacity: 0.85 });

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.55, 24, 16), skinMat);
    head.position.set(0, 1.9, 0);
    group.add(head);

    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.55, 1.3, 8, 16), skinMat);
    torso.position.set(0, 0.8, 0);
    group.add(torso);

    const limbMat = skinMat;
    const armGeo = new THREE.CapsuleGeometry(0.18, 1.1, 6, 12);
    [[-0.85, 0.9, 0, 18], [0.85, 0.9, 0, -18]].forEach(([x, y, z, rotDeg]) => {
        const arm = new THREE.Mesh(armGeo, limbMat);
        arm.position.set(x, y, z);
        arm.rotation.z = THREE.MathUtils.degToRad(rotDeg);
        group.add(arm);
    });
    const legGeo = new THREE.CapsuleGeometry(0.2, 1.2, 6, 12);
    [[-0.3, -0.65, 0], [0.3, -0.65, 0]].forEach(([x, y, z]) => {
        const leg = new THREE.Mesh(legGeo, limbMat);
        leg.position.set(x, y, z);
        group.add(leg);
    });

    // ระบบอวัยวะภายในลำตัว (มองผ่านผิวโปร่งแสง)
    const innerSystem = buildOrganSystem();
    innerSystem.scale.setScalar(0.32);
    innerSystem.position.set(0, 0.9, 0);
    group.add(innerSystem);

    group.position.y = -0.6;
    return group;
}

const BUILDERS = [buildMolecule, buildSingleCell, buildTissue, buildOrgan, buildOrganSystem, buildOrganism];

// ตำแหน่งจัดวางทั้ง 6 ระดับพร้อมกันเป็นเส้นทางซิกแซก (S-shape): แถวบนไล่ซ้าย→ขวา แล้ววกลงแถวล่างขวา→ซ้าย
// ให้เห็นการไล่ระดับจากเล็กไปใหญ่ในภาพเดียวกันทั้งหมด แทนการสลับทีละระดับแบบเดิม
const SLOT_LAYOUT = [
    { x: -6.4, y: 2.6 },  // 0 โมเลกุล
    { x: 0, y: 2.6 },     // 1 เซลล์
    { x: 6.4, y: 2.6 },   // 2 เนื้อเยื่อ
    { x: 6.4, y: -2.6 },  // 3 อวัยวะ
    { x: 0, y: -2.6 },    // 4 ระบบอวัยวะ
    { x: -6.4, y: -2.6 }, // 5 สิ่งมีชีวิต
];
const SLOT_SCALE = [0.85, 0.85, 0.62, 0.8, 0.46, 0.55];

function makeConnector(a, b) {
    const from = new THREE.Vector3(a.x, a.y, 0);
    const to = new THREE.Vector3(b.x, b.y, 0);
    return makeBond(from, to, 0xd8c7a1, 0.09);
}

export function initOrganizationScene(container, options = {}) {
    const { onSelect } = options;

    // กันไว้เผื่อ container ยังไม่มีขนาด (เช่น CSS ยังโหลดไม่เสร็จ) จะได้ไม่วาดฉากขนาด 0x0
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 320;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 1.2, 13);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    renderer.domElement.style.display = 'block';
    renderer.domElement.style.cursor = 'grab';

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 6;
    controls.maxDistance = 26;
    controls.target.set(0, 0, 0);

    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
    dirLight.position.set(4, 6, 8);
    scene.add(dirLight);
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
    fillLight.position.set(-4, -2, -6);
    scene.add(fillLight);

    // เส้นเชื่อมลำดับ 0→1→2→3→4→5 ให้เห็นการไล่ระดับเป็นเส้นทางเดียว
    for (let i = 0; i < SLOT_LAYOUT.length - 1; i++) {
        scene.add(makeConnector(SLOT_LAYOUT[i], SLOT_LAYOUT[i + 1]));
    }

    const slots = BUILDERS.map((build, i) => {
        const slot = new THREE.Group();
        slot.position.set(SLOT_LAYOUT[i].x, SLOT_LAYOUT[i].y, 0);
        slot.userData.levelIndex = i;
        slot.scale.setScalar(SLOT_SCALE[i]);
        slot.add(build());
        scene.add(slot);
        return slot;
    });

    function findLevelIndex(obj) {
        let o = obj;
        while (o) {
            if (o.userData && o.userData.levelIndex !== undefined) return o.userData.levelIndex;
            o = o.parent;
        }
        return null;
    }

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let hoveredIndex = null;
    let pulseIndex = null;
    let pulseT = 0;

    function setPointerFromEvent(event) {
        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    function pickIndex() {
        raycaster.setFromCamera(pointer, camera);
        const hits = raycaster.intersectObjects(scene.children, true);
        for (const hit of hits) {
            const idx = findLevelIndex(hit.object);
            if (idx !== null) return idx;
        }
        return null;
    }

    function screenPosOfSlot(index) {
        const v = new THREE.Vector3();
        slots[index].getWorldPosition(v);
        v.project(camera);
        const rect = renderer.domElement.getBoundingClientRect();
        return {
            x: (v.x * 0.5 + 0.5) * rect.width,
            y: (-v.y * 0.5 + 0.5) * rect.height,
        };
    }

    function triggerSelect(index, screenPos) {
        pulseIndex = index;
        pulseT = 0;
        if (onSelect) onSelect(ORGANIZATION_LEVELS[index], index, screenPos || screenPosOfSlot(index));
    }

    function handleClick(event) {
        const localPos = setPointerFromEvent(event);
        const idx = pickIndex();
        if (idx !== null) triggerSelect(idx, localPos);
    }

    function handlePointerMove(event) {
        setPointerFromEvent(event);
        const idx = pickIndex();
        renderer.domElement.style.cursor = idx !== null ? 'pointer' : 'grab';
        hoveredIndex = idx;
    }

    renderer.domElement.addEventListener('click', handleClick);
    renderer.domElement.addEventListener('pointermove', handlePointerMove);

    let rafId;
    const _tmpScale = new THREE.Vector3();
    function animate() {
        rafId = requestAnimationFrame(animate);
        slots.forEach((slot, i) => {
            slot.children[0].rotation.y += 0.004;
            let targetScale = SLOT_SCALE[i];
            if (pulseIndex === i) {
                pulseT += 0.06;
                targetScale = SLOT_SCALE[i] * (1 + 0.25 * Math.max(0, Math.sin(Math.min(pulseT, Math.PI))));
                if (pulseT >= Math.PI) pulseIndex = null;
            } else if (hoveredIndex === i) {
                targetScale = SLOT_SCALE[i] * 1.12;
            }
            _tmpScale.setScalar(targetScale);
            slot.scale.lerp(_tmpScale, 0.25);
        });
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    function handleResize() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (!w || !h) return;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }
    window.addEventListener('resize', handleResize);

    return {
        selectLevel(index) {
            triggerSelect(index);
        },
        destroy() {
            cancelAnimationFrame(rafId);
            window.removeEventListener('resize', handleResize);
            renderer.domElement.removeEventListener('click', handleClick);
            renderer.domElement.removeEventListener('pointermove', handlePointerMove);
            renderer.dispose();
        },
    };
}
