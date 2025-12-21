import './ZoomControls.css';

interface Props {
    zoom: number;
    onZoomChange: (delta: number) => void;
    onZoomReset: () => void;
}

export function ZoomControls({ zoom, onZoomChange, onZoomReset }: Props) {
    return (
        <div className="zoom-controls">
            <span className="zoom-display">{Math.round(zoom * 100)}%</span>
            <button className="zoom-btn" onClick={() => onZoomChange(0.1)} title="拡大">
                🔍+
            </button>
            <button className="zoom-btn" onClick={() => onZoomChange(-0.1)} title="縮小">
                🔍-
            </button>
            <button className="zoom-btn" onClick={onZoomReset} title="リセット">
                ↺
            </button>
        </div>
    );
}
