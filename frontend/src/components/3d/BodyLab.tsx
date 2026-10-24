// SUGAR — Rebuilt 3D Body Lab with Calibrated Anatomy, Anti-Clipping Camera & Natural Tones
import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Activity,
  Sparkles,
  Info,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { ANATOMICAL_ORGANS } from '../../data/researchData';

export const BodyLab: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [selectedOrganId, setSelectedOrganId] = useState<string>('liver');
  const [hoveredOrganId, setHoveredOrganId] = useState<string | null>(null);
  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [showWireframe, setShowWireframe] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // References for Three.js state
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const organMeshesRef = useRef<Map<string, THREE.Mesh>>(new Map());

  // Camera lerp targets (initial framing: full anatomical torso visible)
  const targetCameraPos = useRef<THREE.Vector3>(new THREE.Vector3(0, 0.35, 4.2));
  const targetControlsCenter = useRef<THREE.Vector3>(new THREE.Vector3(0, 0.25, 0));
  const isTransitioningCamera = useRef<boolean>(false);

  const selectedOrgan =
    ANATOMICAL_ORGANS.find((o) => o.id === selectedOrganId) || ANATOMICAL_ORGANS[0];

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    // 1. Scene setup with subtle depth fog
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070a14);
    scene.fog = new THREE.FogExp2(0x070a14, 0.04);
    sceneRef.current = scene;

    // 2. Camera setup with safe near/far planes to prevent interior clipping
    const camera = new THREE.PerspectiveCamera(
      38,
      container.clientWidth / container.clientHeight,
      0.2, // Near plane at 0.2 prevents surface tearing
      50.0
    );
    camera.position.set(0, 0.35, 4.2);
    cameraRef.current = camera;

    // 3. WebGL Renderer with ACES Tone Mapping
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    rendererRef.current = renderer;

    // 4. OrbitControls with strict minDistance to avoid zooming inside organs
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 2.0; // Strictly prevents camera from cutting into organs
    controls.maxDistance = 5.5; // Bounds zoom-out
    controls.target.set(0, 0.25, 0);
    controlsRef.current = controls;

    // 5. Studio Lighting: Balanced, natural matte illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
    keyLight.position.set(3, 4, 3);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0xa9d4e7, 1.2);
    rimLight.position.set(-3, 2, -3);
    scene.add(rimLight);

    const fillLight = new THREE.DirectionalLight(0x153568, 0.8);
    fillLight.position.set(0, -3, 2);
    scene.add(fillLight);

    // 6. Medical Spatial Grid Floor
    const gridHelper = new THREE.GridHelper(8, 20, 0x153568, 0x0e1c38);
    gridHelper.position.y = -1.25;
    scene.add(gridHelper);

    // 7. Anatomical Reference Cage (Semi-Transparent Holographic Thorax)
    const torsoGroup = new THREE.Group();
    torsoGroup.name = 'torso_silhouette';

    // Rib cage contours
    for (let i = 0; i < 7; i++) {
      const ringGeo = new THREE.TorusGeometry(0.68 - i * 0.02, 0.012, 16, 48);
      ringGeo.scale(1.0, 0.62, 1.0);
      ringGeo.rotateX(Math.PI / 2);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x80b3d0,
        transparent: true,
        opacity: 0.18,
        depthWrite: false, // Prevents occluding organs behind it
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.position.set(0, 0.7 - i * 0.14, 0);
      torsoGroup.add(ringMesh);
    }

    // Spine column indicator
    const spineGeo = new THREE.CylinderGeometry(0.045, 0.05, 1.8, 16);
    const spineMat = new THREE.MeshStandardMaterial({
      color: 0x22324e,
      roughness: 0.8,
      metalness: 0.0,
    });
    const spineMesh = new THREE.Mesh(spineGeo, spineMat);
    spineMesh.position.set(0, 0.35, -0.32);
    torsoGroup.add(spineMesh);

    scene.add(torsoGroup);

    // 8. Construct Individual Selectable Anatomical Organs
    const organMeshes = new Map<string, THREE.Mesh>();

    ANATOMICAL_ORGANS.forEach((organ) => {
      let geo: THREE.BufferGeometry;

      // Anatomically sculpted geometry profiles
      if (organ.id === 'liver') {
        // Asymmetric wedge: large right lobe, tapered left lobe
        geo = new THREE.SphereGeometry(1, 32, 24);
        geo.scale(organ.scale[0], organ.scale[1], organ.scale[2]);
        const pos = geo.attributes.position;
        for (let i = 0; i < pos.count; i++) {
          const x = pos.getX(i);
          if (x < 0) {
            pos.setY(i, pos.getY(i) * 0.62);
            pos.setZ(i, pos.getZ(i) * 0.72);
          }
        }
        geo.computeVertexNormals();
      } else if (organ.id === 'gallbladder') {
        // Pear-shaped gallbladder sac
        geo = new THREE.SphereGeometry(1, 24, 18);
        geo.scale(organ.scale[0], organ.scale[1] * 1.3, organ.scale[2]);
      } else if (organ.id === 'spleen') {
        // Curved crescent spleen
        geo = new THREE.SphereGeometry(1, 28, 20);
        geo.scale(organ.scale[0], organ.scale[1], organ.scale[2]);
        geo.rotateZ(0.25);
      } else if (organ.id === 'stomach') {
        // J-shaped hollow digestive pouch
        geo = new THREE.TorusGeometry(0.3, 0.18, 24, 36, Math.PI * 0.85);
        geo.scale(organ.scale[0], organ.scale[1], organ.scale[2]);
        geo.rotateZ(-0.3);
      } else if (organ.id === 'heart') {
        // Mediastinal conical form
        geo = new THREE.DodecahedronGeometry(0.36, 3);
        geo.scale(organ.scale[0], organ.scale[1] * 1.2, organ.scale[2]);
        geo.rotateZ(-0.2);
      } else if (organ.id === 'lungs') {
        // Bilateral spongy pleural volumes
        geo = new THREE.SphereGeometry(1, 32, 24);
        geo.scale(organ.scale[0], organ.scale[1], organ.scale[2]);
      } else {
        // Kidneys (Reniform bean shape)
        geo = new THREE.SphereGeometry(1, 24, 18);
        geo.scale(organ.scale[0], organ.scale[1] * 1.2, organ.scale[2]);
      }

      // Natural Biological Tissue PBR Material (MATTE, NO SHINY PLASTIC)
      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(organ.naturalColor),
        roughness: 0.78, // Matte natural organic tissue
        metalness: 0.0,  // Zero metallic sheen
        emissive: new THREE.Color(0x000000),
        emissiveIntensity: 0.0,
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(...organ.position);
      mesh.userData = { organId: organ.id, organName: organ.name };

      scene.add(mesh);
      organMeshes.set(organ.id, mesh);
    });

    organMeshesRef.current = organMeshes;

    // 9. Raycasting Setup
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const meshes = Array.from(organMeshes.values());
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const hit = intersects[0].object as THREE.Mesh;
        setHoveredOrganId(hit.userData.organId);
        canvas.style.cursor = 'pointer';
      } else {
        setHoveredOrganId(null);
        canvas.style.cursor = 'grab';
      }
    };

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const meshes = Array.from(organMeshes.values());
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const hit = intersects[0].object as THREE.Mesh;
        selectOrgan(hit.userData.organId);
      }
    };

    canvas.addEventListener('mousemove', handlePointerMove);
    canvas.addEventListener('mousedown', () => (canvas.style.cursor = 'grabbing'));
    canvas.addEventListener('mouseup', () => (canvas.style.cursor = 'grab'));
    canvas.addEventListener('click', handleClick);

    // 10. Animation Loop
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Smooth camera transition toward target organ
      if (isTransitioningCamera.current) {
        camera.position.lerp(targetCameraPos.current, 0.08);
        controls.target.lerp(targetControlsCenter.current, 0.08);

        if (
          camera.position.distanceTo(targetCameraPos.current) < 0.03 &&
          controls.target.distanceTo(targetControlsCenter.current) < 0.03
        ) {
          isTransitioningCamera.current = false;
        }
      }

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handlePointerMove);
      canvas.removeEventListener('click', handleClick);
      renderer.dispose();
    };
  }, []);

  // Update visual state when selected/hovered organ changes
  useEffect(() => {
    organMeshesRef.current.forEach((mesh, id) => {
      const organ = ANATOMICAL_ORGANS.find((o) => o.id === id);
      if (!organ) return;

      const mat = mesh.material as THREE.MeshStandardMaterial;
      const isSelected = id === selectedOrganId;
      const isHovered = id === hoveredOrganId;

      mat.wireframe = showWireframe;

      // PRESERVE NATURAL ANATOMICAL COLOR
      mat.color.set(organ.naturalColor);

      if (isSelected) {
        // Selection highlight: Ice-Blue emissive glow overlay
        mat.emissive.set(0x19166d);
        mat.emissiveIntensity = 0.65;
        mat.roughness = 0.65;
      } else if (isHovered) {
        mat.emissive.set(0x153568);
        mat.emissiveIntensity = 0.35;
        mat.roughness = 0.72;
      } else {
        mat.emissive.set(0x000000);
        mat.emissiveIntensity = 0.0;
        mat.roughness = 0.78;
      }
    });

    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
      controlsRef.current.autoRotateSpeed = 1.0;
    }
  }, [selectedOrganId, hoveredOrganId, autoRotate, showWireframe]);

  // Smooth camera centering with safe distance (prevents interior clipping)
  const selectOrgan = (organId: string) => {
    setSelectedOrganId(organId);
    const organ = ANATOMICAL_ORGANS.find((o) => o.id === organId);
    if (!organ || !cameraRef.current || !controlsRef.current) return;

    const [tx, ty, tz] = organ.cameraTarget;
    targetControlsCenter.current.set(tx, ty, tz);

    // Set camera at a safe viewing distance of 2.6 units (prevents inside-organ clipping)
    targetCameraPos.current.set(tx + 0.3, ty + 0.2, tz + 2.6);
    isTransitioningCamera.current = true;
  };

  const resetCamera = () => {
    targetControlsCenter.current.set(0, 0.25, 0);
    targetCameraPos.current.set(0, 0.35, 4.2);
    isTransitioningCamera.current = true;
  };

  const zoomCamera = (factor: number) => {
    if (!cameraRef.current || !controlsRef.current) return;
    const currentDist = cameraRef.current.position.distanceTo(controlsRef.current.target);
    const newDist = currentDist * factor;
    if (newDist >= 2.0 && newDist <= 5.5) {
      cameraRef.current.position.lerp(controlsRef.current.target, 1 - factor);
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Section Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-3 border-b border-[#153568]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="h1 flex items-center gap-2">
              <Layers className="text-ice" size={26} />
              Human Systems Observatory
            </h1>
            <span className="badge badge-ice">Interactive Anatomy</span>
          </div>
          <p className="text-muted mt-1" style={{ fontSize: '0.92rem' }}>
            Supporting 3D viewer — click organs to explore clinical biomarkers and fibrosis anatomical context. Tissue-calibrated natural pigmentation with ice-blue selection raycasting.
          </p>
        </div>

        {/* Quick Organ Selector Pill Strip */}
        <div className="flex items-center gap-2 flex-wrap">
          {ANATOMICAL_ORGANS.map((organ) => {
            const isSelected = organ.id === selectedOrganId;
            return (
              <button
                key={organ.id}
                onClick={() => selectOrgan(organ.id)}
                style={{
                  background: isSelected ? 'var(--navy-royal)' : 'rgba(16, 16, 82, 0.5)',
                  borderColor: isSelected ? 'var(--ice-blue)' : 'var(--border-subtle)',
                  color: isSelected ? '#ffffff' : 'var(--steel-blue)',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.84rem',
                  fontWeight: 500,
                  border: '1px solid',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.15s ease',
                }}
              >
                <span
                  style={{
                    backgroundColor: organ.naturalColor,
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    border: '1px solid rgba(0,0,0,0.4)',
                  }}
                />
                <span>{organ.name.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3D Canvas Stage */}
      <div ref={containerRef} className="bodylab-stage select-none">
        <canvas ref={canvasRef} className="bodylab-canvas" />

        {/* Top-Left Status & Provenance Badges */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div
            style={{
              background: 'rgba(10, 14, 28, 0.88)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '8px 14px',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.86rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#A9D4E7' }} />
              <span style={{ color: '#ffffff', fontWeight: 600 }}>360° Anatomical Viewer</span>
            </div>
            <span style={{ color: '#80B3D0' }}>|</span>
            <span style={{ color: '#CBD5E1' }}>
              Focused: <strong style={{ color: '#A9D4E7' }}>{selectedOrgan.name}</strong>
            </span>
          </div>

          <div
            style={{
              background: 'rgba(16, 16, 82, 0.85)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.8rem',
              color: '#CBD5E1',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              maxWidth: '380px',
            }}
          >
            <CheckCircle2 size={14} style={{ color: '#A9D4E7', flexShrink: 0 }} />
            <span>
              <strong>Anatomy Engine:</strong> Calibrated schematic organ hierarchy with natural biological pigmentation.
            </span>
          </div>
        </div>

        {/* Top-Right Camera Controls */}
        <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            title="Toggle 360° Rotation"
            className="btn btn-secondary"
            style={{ padding: '8px', minWidth: '36px' }}
          >
            <RotateCcw size={16} />
          </button>
          <button
            onClick={() => setShowWireframe(!showWireframe)}
            title="Toggle Mesh Wireframe"
            className="btn btn-secondary"
            style={{ padding: '8px', minWidth: '36px' }}
          >
            <Layers size={16} />
          </button>
          <button
            onClick={() => zoomCamera(0.85)}
            title="Zoom In"
            className="btn btn-secondary"
            style={{ padding: '8px', minWidth: '36px' }}
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={() => zoomCamera(1.15)}
            title="Zoom Out"
            className="btn btn-secondary"
            style={{ padding: '8px', minWidth: '36px' }}
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={resetCamera}
            title="Reset Camera Framing"
            className="btn btn-secondary"
            style={{ padding: '8px 12px', fontSize: '0.84rem' }}
          >
            Reset
          </button>
          <button
            onClick={toggleFullscreen}
            title="Toggle Fullscreen"
            className="btn btn-secondary"
            style={{ padding: '8px', minWidth: '36px' }}
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>

        {/* Floating Glass-Style Organ Information Panel */}
        <div className="floating-panel">
          {/* Panel Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid var(--navy-clinical)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  backgroundColor: selectedOrgan.naturalColor,
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  border: '2px solid #A9D4E7',
                  boxShadow: '0 0 8px rgba(169, 212, 231, 0.4)',
                }}
              />
              <div>
                <h3 style={{ fontSize: '1.15rem', color: '#ffffff', margin: 0 }}>
                  {selectedOrgan.name}
                </h3>
                <span style={{ fontSize: '0.78rem', color: '#80B3D0', fontWeight: 600, textTransform: 'uppercase' }}>
                  {selectedOrgan.system}
                </span>
              </div>
            </div>

            <span className="badge badge-ice">Focused</span>
          </div>

          {/* Tissue Swatch */}
          <div
            style={{
              marginTop: '12px',
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(16, 16, 82, 0.6)',
              border: '1px solid var(--navy-clinical)',
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.85rem',
            }}
          >
            <span style={{ color: '#80B3D0' }}>Tissue Pigmentation:</span>
            <span style={{ color: '#ffffff', fontFamily: 'JetBrains Mono', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ backgroundColor: selectedOrgan.naturalColor, width: '10px', height: '10px', borderRadius: '50%', display: 'inline-block' }} />
              {selectedOrgan.colorName}
            </span>
          </div>

          {/* Physiological Function */}
          <div style={{ marginTop: '14px' }}>
            <h4 style={{ fontSize: '0.85rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={14} />
              Physiological Function
            </h4>
            <p style={{ fontSize: '0.9rem', color: '#CBD5E1', lineHeight: '1.55' }}>
              {selectedOrgan.function}
            </p>
          </div>

          {/* Biomarkers */}
          <div style={{ marginTop: '16px' }}>
            <h4 style={{ fontSize: '0.85rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={14} />
              Correlated Clinical Biomarkers
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {selectedOrgan.biomarkers.map((bm, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'rgba(7, 10, 20, 0.75)',
                    border: '1px solid var(--navy-clinical)',
                    borderRadius: '6px',
                    padding: '8px 12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span style={{ color: '#ffffff', fontWeight: 600, fontSize: '0.88rem' }}>{bm.name}</span>
                    <span style={{ fontFamily: 'JetBrains Mono', color: '#A9D4E7', fontSize: '0.82rem' }}>{bm.normalRange}</span>
                  </div>
                  <p style={{ fontSize: '0.84rem', color: '#80B3D0', margin: 0, lineHeight: '1.4' }}>
                    {bm.fibrosisSignificance}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Fibrosis Staging Relevance */}
          <div
            style={{
              marginTop: '16px',
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(25, 22, 109, 0.35)',
              border: '1px solid var(--navy-clinical)',
            }}
          >
            <h4 style={{ fontSize: '0.82rem', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={13} />
              Fibrosis Progression Context
            </h4>
            <p style={{ fontSize: '0.86rem', color: '#CBD5E1', lineHeight: '1.45', margin: 0 }}>
              {selectedOrgan.fibrosisNotes}
            </p>
          </div>

          {/* Scientific Disclaimer */}
          <p style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--navy-clinical)', fontSize: '0.78rem', color: '#80B3D0', fontStyle: 'italic', margin: 0 }}>
            {selectedOrgan.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
};
