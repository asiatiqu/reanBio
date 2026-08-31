// 📌 สื่อ 3D Interactive: ระดับการจัดระบบของสิ่งมีชีวิต (โมเลกุล → เซลล์ → เนื้อเยื่อ → อวัยวะ → ระบบอวัยวะ → สิ่งมีชีวิต)
// สร้างจาก Three.js ล้วน ๆ ด้วยรูปทรงพื้นฐาน (sphere/cylinder/torus) ไม่ต้องพึ่งไฟล์โมเดล 3D ภายนอก
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

function makeBond(from, to, color = 0xcccccc) {
    const dir = new THREE.Vector3().subVectors(to, from);
    const len = dir.length();
    const geo = new THREE.CylinderGeometry(0.05, 0.05, len, 8);
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

export function initOrganizationScene(container) {
    // กันไว้เผื่อ container ยังไม่มีขนาด (เช่น CSS ยังโหลดไม่เสร็จ) จะได้ไม่วาดฉากขนาด 0x0
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 320;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(3.2, 2, 4.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 2;
    controls.maxDistance = 12;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.4;

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
    dirLight.position.set(4, 6, 5);
    scene.add(dirLight);
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
    fillLight.position.set(-4, -2, -5);
    scene.add(fillLight);

    const levelGroups = BUILDERS.map((build) => {
        const g = build();
        g.visible = false;
        scene.add(g);
        return g;
    });

    let currentIndex = 0;
    function showLevel(index) {
        currentIndex = ((index % levelGroups.length) + levelGroups.length) % levelGroups.length;
        levelGroups.forEach((g, i) => { g.visible = i === currentIndex; });
        controls.autoRotate = true;
        return ORGANIZATION_LEVELS[currentIndex];
    }
    showLevel(0);

    let rafId;
    function animate() {
        rafId = requestAnimationFrame(animate);
        const active = levelGroups[currentIndex];
        if (active) active.rotation.y += 0.0015;
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    function handleResize() {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }
    window.addEventListener('resize', handleResize);

    return {
        showLevel,
        getCurrentIndex: () => currentIndex,
        destroy() {
            cancelAnimationFrame(rafId);
            window.removeEventListener('resize', handleResize);
            renderer.dispose();
        },
    };
}
