"""Float64 Cartesian frame and rigid-coordinate transformation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from quantum_space_agi.scientific.errors import ScientificError, ScientificErrorCode
from quantum_space_agi.scientific.units import Unit, get_unit

Vector = NDArray[np.float64]
Matrix = NDArray[np.float64]
ORTHOGONAL_TOLERANCE = 1e-9


def _contains_boolean(value) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "b":
            return True
        if value.dtype.kind == "O":
            return any(_contains_boolean(component) for component in value.flat)
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_boolean(component) for component in value)
    return False


def _validate_angle(angle: Real, *, field: str = "angle_radians") -> float:
    if isinstance(angle, (bool, np.bool_)) or not isinstance(angle, Real):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Rotation angle must be a real number.",
            field=field,
            expected="real finite angle in radians",
            received=type(angle).__name__,
        )
    result = float(angle)
    if not np.isfinite(result):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Rotation angle must be finite.",
            field=field,
            expected="finite radians",
            received=result,
        )
    return result


def _validate_axes(axes: Sequence[str]) -> tuple[str, str, str]:
    if not isinstance(axes, (tuple, list)) or len(axes) != 3:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Axes must contain exactly three labels.",
            field="axes",
            expected=("X", "Y", "Z"),
            received=axes,
        )
    normalized = tuple(str(axis).upper() for axis in axes)
    if set(normalized) != {"X", "Y", "Z"} or len(set(normalized)) != 3:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Axes must be a permutation of X, Y, and Z.",
            field="axes",
            expected=("X", "Y", "Z"),
            received=axes,
        )
    return normalized


@dataclass(frozen=True, slots=True)
class CoordinateFrame:
    """Named Cartesian frame metadata."""

    name: str
    unit: Unit = get_unit("m")
    axes: tuple[str, str, str] = ("X", "Y", "Z")
    handedness: str = "right"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Frame name must be a non-empty string.",
                field="name",
                expected="non-empty frame name",
                received=self.name,
            )
        if not isinstance(self.unit, Unit):
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Frame unit must be a Unit instance.",
                field="unit",
                expected="Unit",
                received=type(self.unit).__name__,
            )
        if tuple(self.unit.dimensions) != (1, 0, 0, 0, 0, 0, 0):
            raise ScientificError(
                ScientificErrorCode.UNIT_MISMATCH,
                "Cartesian frame coordinates must use a length unit.",
                field="unit",
                expected="length unit",
                received=self.unit.symbol,
            )
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "axes", _validate_axes(self.axes))
        handedness = str(self.handedness).lower().strip()
        if handedness not in ("right", "left"):
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Frame handedness must be 'right' or 'left'.",
                field="handedness",
                expected="right or left",
                received=self.handedness,
            )
        object.__setattr__(self, "handedness", handedness)


Frame = CoordinateFrame


def _validate_vector(values: Sequence[Real] | NDArray[np.generic], *, field: str = "vector") -> Vector:
    if isinstance(values, (str, bytes, bool)) or _contains_boolean(values):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Coordinate vector must contain real numeric components.",
            field=field,
            expected="three real components",
            received=type(values).__name__,
        )
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Coordinate vector is not array-like.",
            field=field,
            expected="three real components",
            received=type(values).__name__,
        ) from exc
    if array.shape != (3,) or np.iscomplexobj(array) or array.dtype.kind == "b":
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Coordinate vector must be a three-component real array.",
            field=field,
            expected="shape (3,)",
            received=array.shape,
        )
    try:
        result = np.array(array, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Coordinate components must be Float64-compatible real values.",
            field=field,
            expected="three real components",
            received=array.dtype.name,
        ) from exc
    if not np.all(np.isfinite(result)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Coordinate components must be finite.",
            field=field,
            expected="finite Float64 components",
            received=result.tolist(),
        )
    return result


def _validate_rotation_matrix(values: Sequence[Sequence[Real]] | NDArray[np.generic], *, field: str = "rotation") -> Matrix:
    if _contains_boolean(values):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Rotation components must be real numeric values, not booleans.",
            field=field,
            expected="real 3x3 matrix",
            received=type(values).__name__,
        )
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Rotation must be a 3x3 matrix.",
            field=field,
            expected="shape (3, 3)",
            received=type(values).__name__,
        ) from exc
    if array.shape != (3, 3) or np.iscomplexobj(array) or array.dtype.kind == "b":
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Rotation must be a three-by-three real matrix.",
            field=field,
            expected="shape (3, 3)",
            received=array.shape,
        )
    try:
        result = np.array(array, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Rotation components must be real Float64 values.",
            field=field,
            expected="real 3x3 matrix",
            received=array.dtype.name,
        ) from exc
    if not np.all(np.isfinite(result)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Rotation components must be finite.",
            field=field,
            expected="finite Float64 matrix",
            received=result.tolist(),
        )
    gram_error = np.max(np.abs(result.T @ result - np.eye(3, dtype=np.float64)))
    det = float(np.linalg.det(result))
    if not np.isfinite(det) or gram_error > ORTHOGONAL_TOLERANCE or abs(det - 1.0) > ORTHOGONAL_TOLERANCE:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Rotation matrix must be right-handed and orthogonal.",
            field=field,
            expected="R.T @ R = I and det(R) = +1",
            received={"orthogonality_error": float(gram_error), "determinant": det},
        )
    return result


def active_rotation_matrix_x(angle_radians: Real) -> Matrix:
    """Active right-hand rotation by +angle about fixed X, in radians."""

    angle = _validate_angle(angle_radians)
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c)), dtype=np.float64)


def active_rotation_matrix_y(angle_radians: Real) -> Matrix:
    """Active right-hand rotation by +angle about fixed Y, in radians."""

    angle = _validate_angle(angle_radians)
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c)), dtype=np.float64)


def active_rotation_matrix_z(angle_radians: Real) -> Matrix:
    """Active right-hand rotation by +angle about fixed Z, in radians."""

    angle = _validate_angle(angle_radians)
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)), dtype=np.float64)


rotation_matrix_x = active_rotation_matrix_x
rotation_matrix_y = active_rotation_matrix_y
rotation_matrix_z = active_rotation_matrix_z


def passive_rotation_matrix_x(angle_radians: Real) -> Matrix:
    return active_rotation_matrix_x(angle_radians).T.copy()


def passive_rotation_matrix_y(angle_radians: Real) -> Matrix:
    return active_rotation_matrix_y(angle_radians).T.copy()


def passive_rotation_matrix_z(angle_radians: Real) -> Matrix:
    return active_rotation_matrix_z(angle_radians).T.copy()


def euler_rotation_matrix(sequence: str, angles_radians: Sequence[Real], *, extrinsic: bool = True) -> Matrix:
    """Compose active right-hand rotations; extrinsic fixed-axis sequence is default."""

    if not isinstance(sequence, str) or len(sequence) != 3 or any(axis.upper() not in "XYZ" for axis in sequence):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Euler sequence must contain three axes from X, Y, and Z.",
            field="sequence",
            expected="XYZ, ZYX, etc.",
            received=sequence,
        )
    if isinstance(angles_radians, (str, bytes)):
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Euler angles must be a three-value sequence.",
            field="angles_radians",
            expected="three radians",
            received=type(angles_radians).__name__,
        )
    try:
        raw = tuple(angles_radians)
    except TypeError as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Euler angles must be a three-value sequence.",
            field="angles_radians",
            expected="three radians",
            received=type(angles_radians).__name__,
        ) from exc
    if len(raw) != 3:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Euler angles must contain exactly three values.",
            field="angles_radians",
            expected="three radians",
            received=len(raw),
        )
    matrices = []
    for axis, angle in zip(sequence.upper(), raw):
        if axis == "X":
            matrices.append(active_rotation_matrix_x(angle))
        elif axis == "Y":
            matrices.append(active_rotation_matrix_y(angle))
        else:
            matrices.append(active_rotation_matrix_z(angle))
    result = np.eye(3, dtype=np.float64)
    if extrinsic:
        for matrix in matrices:
            result = matrix @ result
    else:
        for matrix in reversed(matrices):
            result = result @ matrix
    return _validate_rotation_matrix(result)


def _coerce_frame(frame: CoordinateFrame | str, *, unit: str | Unit = "m") -> CoordinateFrame:
    if isinstance(frame, CoordinateFrame):
        return frame
    if isinstance(frame, str) and frame.strip():
        return CoordinateFrame(frame, unit=get_unit(unit))
    raise ScientificError(
        ScientificErrorCode.INVALID_STATE,
        "Frame must be a CoordinateFrame or a non-empty frame name.",
        field="frame",
        expected="CoordinateFrame or frame name",
        received=type(frame).__name__,
    )


@dataclass(frozen=True, slots=True)
class RigidTransform:
    """Rigid map x_to = R @ x_from + t; translation is in to_frame units."""

    from_frame: CoordinateFrame
    to_frame: CoordinateFrame
    rotation: Matrix
    translation: Vector

    def __post_init__(self) -> None:
        source = _coerce_frame(self.from_frame)
        target = _coerce_frame(self.to_frame)
        if source.handedness != "right" or target.handedness != "right":
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Rigid transforms require right-handed Cartesian frames.",
                field="frame.handedness",
                expected="right-handed frames",
                received=(source.handedness, target.handedness),
            )
        object.__setattr__(self, "from_frame", source)
        object.__setattr__(self, "to_frame", target)
        object.__setattr__(self, "rotation", _validate_rotation_matrix(self.rotation))
        object.__setattr__(self, "translation", _validate_vector(self.translation, field="translation"))
        self.rotation.setflags(write=False)
        self.translation.setflags(write=False)


def create_transform(
    from_frame: CoordinateFrame | str,
    to_frame: CoordinateFrame | str,
    *,
    rotation: Sequence[Sequence[Real]] | NDArray[np.generic] | None = None,
    translation: Sequence[Real] | NDArray[np.generic] | None = None,
) -> RigidTransform:
    source = _coerce_frame(from_frame)
    target = _coerce_frame(to_frame)
    r = np.eye(3, dtype=np.float64) if rotation is None else _validate_rotation_matrix(rotation)
    t = np.zeros(3, dtype=np.float64) if translation is None else _validate_vector(translation, field="translation")
    return RigidTransform(source, target, r, t)


def _unit_scale(from_unit: Unit, to_unit: Unit) -> float:
    if tuple(from_unit.dimensions) != tuple(to_unit.dimensions):
        raise ScientificError(
            ScientificErrorCode.UNIT_MISMATCH,
            "Frame units have incompatible dimensions.",
            field="frame.unit",
            expected=to_unit.symbol,
            received=from_unit.symbol,
        )
    scale = float(from_unit.scale / to_unit.scale)
    if not np.isfinite(scale) or scale <= 0.0:
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Unit conversion scale is invalid.",
            field="frame.unit",
            expected="positive finite scale",
            received=scale,
        )
    return scale


def transform_point(transform: RigidTransform, point: Sequence[Real] | NDArray[np.generic]) -> Vector:
    if not isinstance(transform, RigidTransform):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "transform must be a RigidTransform.",
            field="transform",
            expected="RigidTransform",
            received=type(transform).__name__,
        )
    source = _validate_vector(point, field="point")
    source_in_target_units = source * _unit_scale(transform.from_frame.unit, transform.to_frame.unit)
    result = transform.rotation @ source_in_target_units + transform.translation
    if not np.all(np.isfinite(result)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Transform produced a non-finite point.",
            field="point",
            expected="finite Float64 components",
            received=result.tolist(),
        )
    return np.array(result, dtype=np.float64, copy=True)


def transform_vector(transform: RigidTransform, vector: Sequence[Real] | NDArray[np.generic]) -> Vector:
    """Rotate a free vector without applying translation."""

    if not isinstance(transform, RigidTransform):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "transform must be a RigidTransform.",
            field="transform",
            expected="RigidTransform",
            received=type(transform).__name__,
        )
    source = _validate_vector(vector, field="vector")
    source_in_target_units = source * _unit_scale(transform.from_frame.unit, transform.to_frame.unit)
    result = transform.rotation @ source_in_target_units
    if not np.all(np.isfinite(result)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Transform produced a non-finite vector.",
            field="vector",
            expected="finite Float64 components",
            received=result.tolist(),
        )
    return np.array(result, dtype=np.float64, copy=True)


def inverse_transform(transform: RigidTransform) -> RigidTransform:
    """Invert x_to = R*x_from+t as x_from=scale(R.T*(x_to-t))."""

    if not isinstance(transform, RigidTransform):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "transform must be a RigidTransform.",
            field="transform",
            expected="RigidTransform",
            received=type(transform).__name__,
        )
    inverse_rotation = transform.rotation.T.copy()
    scale = _unit_scale(transform.to_frame.unit, transform.from_frame.unit)
    translation = -scale * (inverse_rotation @ transform.translation)
    if not np.all(np.isfinite(translation)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Inverse transform produced a non-finite translation.",
            field="translation",
            expected="finite Float64 components",
            received=translation.tolist(),
        )
    return RigidTransform(transform.to_frame, transform.from_frame, inverse_rotation, translation)


def compose_transforms(outer: RigidTransform, inner: RigidTransform) -> RigidTransform:
    """Return outer(inner(x)); both transforms share the connected frame convention."""

    if not isinstance(outer, RigidTransform) or not isinstance(inner, RigidTransform):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Both inputs must be RigidTransform instances.",
            field="transform",
            expected="RigidTransform pair",
            received=(type(outer).__name__, type(inner).__name__),
        )
    if outer.from_frame.name != inner.to_frame.name:
        raise ScientificError(
            ScientificErrorCode.FRAME_MISMATCH,
            "Transforms cannot be composed because frame names do not connect.",
            field="frame",
            expected=inner.to_frame.name,
            received=outer.from_frame.name,
        )
    if outer.from_frame.axes != inner.to_frame.axes or outer.from_frame.handedness != inner.to_frame.handedness:
        raise ScientificError(
            ScientificErrorCode.FRAME_MISMATCH,
            "Connected frames do not use compatible axis conventions.",
            field="frame",
            expected=inner.to_frame.name,
            received=outer.from_frame.name,
        )
    rotation = outer.rotation @ inner.rotation
    middle_translation = inner.translation * _unit_scale(inner.to_frame.unit, outer.to_frame.unit)
    translation = outer.rotation @ middle_translation + outer.translation
    if not np.all(np.isfinite(rotation)) or not np.all(np.isfinite(translation)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Composition produced a non-finite result.",
            field="composition",
            expected="finite Float64 transform",
            received={"rotation": rotation.tolist(), "translation": translation.tolist()},
        )
    return RigidTransform(inner.from_frame, outer.to_frame, rotation, translation)


apply_transform = transform_point
compose = compose_transforms
inverse = inverse_transform
apply_rotation = transform_vector

__all__ = [
    "Vector",
    "Matrix",
    "CoordinateFrame",
    "Frame",
    "RigidTransform",
    "ORTHOGONAL_TOLERANCE",
    "active_rotation_matrix_x",
    "active_rotation_matrix_y",
    "active_rotation_matrix_z",
    "rotation_matrix_x",
    "rotation_matrix_y",
    "rotation_matrix_z",
    "passive_rotation_matrix_x",
    "passive_rotation_matrix_y",
    "passive_rotation_matrix_z",
    "euler_rotation_matrix",
    "create_transform",
    "transform_point",
    "transform_vector",
    "inverse_transform",
    "compose_transforms",
    "apply_transform",
    "compose",
    "inverse",
    "apply_rotation",
]
