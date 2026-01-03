import { useRef, useEffect, useState, useCallback, useMemo } from "react";
import Globe from "react-globe.gl";
import { useNavigate } from "react-router-dom";
import {
  LANGUAGE_LOCATIONS,
  getLanguageByName,
} from "../../data/languageLocations";
import type { SimilarityMatrix } from "../../types";
import "./Globe.css";

export interface DistanceFilter {
  veryClose: boolean; // < 0.05
  close: boolean; // < 0.1
  slightlyClose: boolean; // < 0.3
  slightlyFar: boolean; // < 0.5
  far: boolean; // < 0.7
  veryFar: boolean; // >= 0.7
}

interface Props {
  similarityData: SimilarityMatrix;
  onLanguageClick: (langName: string, nodeCode: string) => void;
  distanceFilter: DistanceFilter;
  selectedNodeCode: string | null;
}

interface ArcData {
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  color: string;
  lang1: string;
  lang2: string;
  distance: number;
  geoDistance: number;
  category:
    | "veryClose"
    | "close"
    | "slightlyClose"
    | "slightlyFar"
    | "far"
    | "veryFar"
    | "same";
  clickable: boolean;
  node1Code: string;
  node2Code: string;
}

interface PointData {
  lat: number;
  lng: number;
  name: string;
  nameJa: string;
  code: string;
  country: string;
  size: number;
  color: string;
  isPrimary: boolean;
}

function calculateGeoDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function normalizeGeoDistance(km: number): number {
  return Math.min(km / 20000, 1);
}

function getDistanceCategory(
  distance: number,
): "veryClose" | "close" | "slightlyClose" | "slightlyFar" | "far" | "veryFar" {
  if (distance < 0.05) return "veryClose";
  if (distance < 0.1) return "close";
  if (distance < 0.3) return "slightlyClose";
  if (distance < 0.5) return "slightlyFar";
  if (distance < 0.7) return "far";
  return "veryFar";
}

function getDistanceOpacity(distance: number): number {
  // 距離0（青）→ 0.8、距離0.5（赤）→ 0.2
  return Math.max(0.2, 0.8 - distance * 1.2);
}

function getDistanceColor(distance: number, opacity: number): string {
  const t = Math.min(Math.max(distance * 2, 0), 1);

  let r: number, g: number, b: number;

  if (t < 0.25) {
    r = Math.round(59 + t * 4 * (34 - 59));
    g = Math.round(130 + t * 4 * (197 - 130));
    b = Math.round(246 + t * 4 * (94 - 246));
  } else if (t < 0.5) {
    const tt = (t - 0.25) * 4;
    r = Math.round(34 + tt * (74 - 34));
    g = Math.round(197 + tt * (222 - 197));
    b = Math.round(94 + tt * (128 - 94));
  } else if (t < 0.75) {
    const tt = (t - 0.5) * 4;
    r = Math.round(74 + tt * (250 - 74));
    g = Math.round(222 + tt * (204 - 222));
    b = Math.round(128 + tt * (21 - 128));
  } else {
    const tt = (t - 0.75) * 4;
    r = Math.round(250 + tt * (239 - 250));
    g = Math.round(204 + tt * (68 - 204));
    b = Math.round(21 + tt * (68 - 21));
  }

  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

function getArcAltitude(geoDistanceNormalized: number): number {
  return 0.02 + geoDistanceNormalized * 0.35;
}

export function GlobeVisualization({
  similarityData,
  onLanguageClick,
  distanceFilter,
  selectedNodeCode,
}: Props) {
  // react-globe.gl doesn't export proper ref types
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const globeRef = useRef<any>(null);
  const navigate = useNavigate();
  const [hoverArc, setHoverArc] = useState<ArcData | null>(null);
  const [globeReady, setGlobeReady] = useState(false);

  useEffect(() => {
    if (globeRef.current && globeReady) {
      globeRef.current.pointOfView({ lat: 35, lng: 139, altitude: 2.5 }, 1000);
    }
  }, [globeReady]);

  const pointsData: PointData[] = useMemo(() => {
    return LANGUAGE_LOCATIONS.map((lang) => ({
      lat: lang.lat,
      lng: lang.lng,
      name: lang.name,
      nameJa: lang.nameJa,
      code: lang.code,
      country: lang.country,
      size: lang.isPrimary ? 0.5 : 0.35,
      color:
        selectedNodeCode === lang.code
          ? "#22c55e"
          : lang.isPrimary
            ? "#60a5fa"
            : "#94a3b8",
      isPrimary: lang.isPrimary,
    }));
  }, [selectedNodeCode]);

  const arcsData: ArcData[] = useMemo(() => {
    const arcs: ArcData[] = [];
    const allNodes = LANGUAGE_LOCATIONS;

    // ==========================================
    // 1. 同一言語間の接続（常に表示）
    // ==========================================
    for (let i = 0; i < allNodes.length; i++) {
      for (let j = i + 1; j < allNodes.length; j++) {
        const node1 = allNodes[i];
        const node2 = allNodes[j];

        if (
          node1.primaryCode === node2.code ||
          node2.primaryCode === node1.code ||
          (node1.primaryCode && node1.primaryCode === node2.primaryCode)
        ) {
          const geoDistance = calculateGeoDistance(
            node1.lat,
            node1.lng,
            node2.lat,
            node2.lng,
          );
          const geoDistanceNorm = normalizeGeoDistance(geoDistance);

          arcs.push({
            startLat: node1.lat,
            startLng: node1.lng,
            endLat: node2.lat,
            endLng: node2.lng,
            color: "rgba(148, 163, 184, 0.2)",
            lang1: node1.name,
            lang2: node2.name,
            distance: 0,
            geoDistance: geoDistanceNorm,
            category: "same",
            clickable: false,
            node1Code: node1.code,
            node2Code: node2.code,
          });
        }
      }
    }

    // ==========================================
    // 2. 言語間の類似度線（全ペア、フィルター適用）
    // ==========================================

    // 選択されたノードがあれば、そのノードの線のみ表示するためのフィルタ用
    // selectedNodeCodeがnullなら全表示
    const targetNodeCode = selectedNodeCode;

    for (let i = 0; i < allNodes.length; i++) {
      for (let j = i + 1; j < allNodes.length; j++) {
        const node1 = allNodes[i];
        const node2 = allNodes[j];

        // 選択モード時: 関係ないペアはスキップ
        if (targetNodeCode) {
          if (node1.code !== targetNodeCode && node2.code !== targetNodeCode) {
            continue;
          }
        }

        // 同一言語はスキップ（処理済み）
        if (
          node1.primaryCode === node2.code ||
          node2.primaryCode === node1.code ||
          (node1.primaryCode && node1.primaryCode === node2.primaryCode)
        ) {
          continue;
        }

        const lang1Name = node1.isPrimary
          ? node1.name
          : LANGUAGE_LOCATIONS.find((l) => l.code === node1.primaryCode)?.name;
        const lang2Name = node2.isPrimary
          ? node2.name
          : LANGUAGE_LOCATIONS.find((l) => l.code === node2.primaryCode)?.name;

        if (!lang1Name || !lang2Name) continue;

        const distance = similarityData[lang1Name]?.[lang2Name];
        if (distance === undefined || distance === null) continue;

        const category = getDistanceCategory(distance);

        // ノード選択時はフィルター無視、未選択時のみフィルターを適用
        if (!targetNodeCode && !distanceFilter[category]) continue;

        const geoDistance = calculateGeoDistance(
          node1.lat,
          node1.lng,
          node2.lat,
          node2.lng,
        );
        const geoDistanceNorm = normalizeGeoDistance(geoDistance);
        const opacity = getDistanceOpacity(distance);

        arcs.push({
          startLat: node1.lat,
          startLng: node1.lng,
          endLat: node2.lat,
          endLng: node2.lng,
          color: getDistanceColor(distance, opacity),
          lang1: node1.name,
          lang2: node2.name,
          distance,
          geoDistance: geoDistanceNorm,
          category,
          clickable: true,
          node1Code: node1.code,
          node2Code: node2.code,
        });
      }
    }

    return arcs;
  }, [similarityData, distanceFilter, selectedNodeCode]);

  const handleArcClick = useCallback(
    (arc: ArcData) => {
      if (!arc.clickable) return;

      const lang1 = getLanguageByName(arc.lang1);
      const lang2 = getLanguageByName(arc.lang2);
      if (lang1 && lang2) {
        navigate("/compare/" + lang1.code + "/" + lang2.code);
      }
    },
    [navigate],
  );

  const handlePointClick = useCallback(
    (point: PointData) => {
      onLanguageClick(point.name, point.code);
    },
    [onLanguageClick],
  );

  return (
    <div className="globe-container">
      <Globe
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={pointsData}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointAltitude={0.01}
        // react-globe.gl callback types are not precise
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        pointRadius={(d: any) => (d.code === selectedNodeCode ? 0.7 : d.size)}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        pointLabel={(d: any) => {
          return (
            '<div class="globe-tooltip"><div class="tooltip-title">' +
            d.nameJa +
            '</div><div class="tooltip-subtitle">' +
            d.country +
            "</div></div>"
          );
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onPointClick={(point: any) => handlePointClick(point as PointData)}
        arcsData={arcsData}
        arcStartLat="startLat"
        arcStartLng="startLng"
        arcEndLat="endLat"
        arcEndLng="endLng"
        arcColor="color"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        arcAltitude={(d: any) => {
          const arc = d as ArcData;
          return arc.category === "same"
            ? 0.01
            : getArcAltitude(arc.geoDistance);
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        arcStroke={(d: any) => {
          const arc = d as ArcData;
          // 固定の細めの線
          return arc.category === "same" ? 0.08 : 0.25;
        }}
        arcDashLength={1}
        arcDashGap={0}
        arcDashAnimateTime={0}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        arcLabel={(d: any) => {
          if (!d.clickable) return "";
          return (
            '<div class="globe-tooltip arc-tooltip"><div class="tooltip-title">' +
            d.lang1 +
            " ↔ " +
            d.lang2 +
            '</div><div class="tooltip-distance">距離: ' +
            d.distance.toFixed(4) +
            '</div><div class="tooltip-hint">クリックで詳細比較</div></div>'
          );
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onArcClick={(arc: any) => handleArcClick(arc as ArcData)}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onArcHover={(arc: any) =>
          setHoverArc(arc?.clickable ? (arc as ArcData) : null)
        }
        atmosphereColor="#3b82f6"
        atmosphereAltitude={0.15}
        onGlobeReady={() => setGlobeReady(true)}
      />

      {hoverArc && (
        <div className="arc-info-panel">
          <span className="arc-languages">
            {hoverArc.lang1} ↔ {hoverArc.lang2}
          </span>
          <span className="arc-distance">
            距離: {hoverArc.distance.toFixed(4)}
          </span>
        </div>
      )}
    </div>
  );
}
