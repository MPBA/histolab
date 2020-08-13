import os
from unittest.mock import call

import numpy as np
import pytest

from histolab.exceptions import LevelError
from histolab.slide import Slide
from histolab.tile import Tile
from histolab.tiler import GridTiler, RandomTiler, Tiler
from histolab.types import CoordinatePair

from ..unitutil import (
    ANY,
    NpArrayMock,
    PILImageMock,
    function_mock,
    initializer_mock,
    method_mock,
    property_mock,
)


class Describe_RandomTiler(object):
    def it_constructs_from_args(self, request):
        _init = initializer_mock(request, RandomTiler)

        random_tiler = RandomTiler((512, 512), 10, 2, 7, True, "", ".png", 1e4)

        _init.assert_called_once_with(ANY, (512, 512), 10, 2, 7, True, "", ".png", 1e4)
        assert isinstance(random_tiler, RandomTiler)
        assert isinstance(random_tiler, Tiler)

    def but_it_has_wrong_tile_size_value(self, request):
        with pytest.raises(ValueError) as err:
            RandomTiler((512, -1), 10, 0)

        assert isinstance(err.value, ValueError)
        assert str(err.value) == "Tile size must be greater than 0 ((512, -1))"

    def or_it_has_not_available_level_value(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_50X50_RGB_RANDOM_COLOR
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        random_tiler = RandomTiler((512, 512), 10, 3)

        with pytest.raises(LevelError) as err:
            random_tiler.extract(slide)

        assert isinstance(err.value, LevelError)
        assert str(err.value) == "Level 3 not available. Number of available levels: 1"

    def or_it_has_negative_level_value(self, request):
        with pytest.raises(LevelError) as err:
            RandomTiler((512, 512), 10, -1)

        assert isinstance(err.value, LevelError)
        assert str(err.value) == "Level cannot be negative (-1)"

    def or_it_has_wrong_max_iter(self, request):
        with pytest.raises(ValueError) as err:
            RandomTiler((512, 512), 10, 0, max_iter=3)

        assert isinstance(err.value, ValueError)
        assert (
            str(err.value)
            == "The maximum number of iterations (3) must be grater than or equal to the maximum number of tiles (10)."
        )

    def or_it_has_wrong_seed(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_50X50_RGB_RANDOM_COLOR
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        random_tiler = RandomTiler((512, 512), 10, 0, seed=-1)

        with pytest.raises(ValueError) as err:
            random_tiler.extract(slide)

        assert isinstance(err.value, ValueError)
        assert str(err.value) == "Seed must be between 0 and 2**32 - 1"

    @pytest.mark.parametrize("tile_size", ((512, 512), (128, 128), (10, 10)))
    def it_knows_its_tile_size(self, request, tile_size):
        random_tiler = RandomTiler(tile_size, 10, 0)

        tile_size_ = random_tiler.tile_size

        assert type(tile_size_) == tuple
        assert tile_size_ == tile_size

    @pytest.mark.parametrize("max_iter", (1000, 10, 3000))
    def it_knows_its_max_iter(self, request, max_iter):
        random_tiler = RandomTiler((128, 128), 10, 0, max_iter=max_iter)

        max_iter_ = random_tiler.max_iter

        assert type(max_iter_) == int
        assert max_iter_ == max_iter

    def it_knows_its_tile_filename(self, request, tile_filename_fixture):
        (
            tile_size,
            n_tiles,
            level,
            seed,
            check_tissue,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        ) = tile_filename_fixture
        random_tiler = RandomTiler(
            tile_size, n_tiles, level, seed, check_tissue, prefix, suffix
        )

        _filename = random_tiler._tile_filename(tile_coords, tiles_counter)

        assert type(_filename) == str
        assert _filename == expected_filename

    def it_can_generate_random_coordinates(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _box_mask_thumb = method_mock(request, RandomTiler, "box_mask_thumb")
        _box_mask_thumb.return_value = NpArrayMock.ONES_500X500_BOOL
        _tile_size = property_mock(request, RandomTiler, "tile_size")
        _tile_size.return_value = (128, 128)
        _np_random_choice1 = function_mock(request, "numpy.random.choice")
        _np_random_choice1.return_value = 0
        _np_random_choice2 = function_mock(request, "numpy.random.choice")
        _np_random_choice2.return_value = 0
        _scale_coordinates = function_mock(request, "histolab.tiler.scale_coordinates")
        random_tiler = RandomTiler((128, 128), 10, 0)

        random_tiler._random_tile_coordinates(slide)

        _box_mask_thumb.assert_called_once_with(random_tiler, slide)
        _tile_size.assert_has_calls([call((128, 128))])
        _scale_coordinates.assert_called_once_with(
            reference_coords=CoordinatePair(x_ul=0, y_ul=0, x_br=128, y_br=128),
            reference_size=(500, 500),
            target_size=(500, 500),
        )

    @pytest.mark.parametrize(
        "check_tissue, expected_box",
        (
            (False, NpArrayMock.RANDOM_500X500_BOOL),
            (True, NpArrayMock.RANDOM_500X500_BOOL),
        ),
    )
    def it_knows_its_box_mask(self, request, tmpdir, check_tissue, expected_box):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _biggest_tissue_box_mask = property_mock(
            request, Slide, "biggest_tissue_box_mask"
        )
        _biggest_tissue_box_mask.return_value = expected_box
        random_tiler = RandomTiler((128, 128), 10, 0, check_tissue=check_tissue)

        box_mask = random_tiler.box_mask_thumb(slide)

        _biggest_tissue_box_mask.assert_called_once_with()
        assert type(box_mask) == np.ndarray
        np.testing.assert_array_almost_equal(box_mask, expected_box)

    @pytest.mark.parametrize(
        "coords1, coords2, check_tissue, has_enough_tissue, max_iter, expected_n_tiles",
        (
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [True, True],
                10,
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [True, False],
                2,
                1,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(5900, 6000, 5900, 6000),  # wrong coordinates
                True,
                [True, True],
                2,
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                False,
                [True, True],
                10,
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                False,
                [False, False],
                10,
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [False, False],
                10,
                0,
            ),
        ),
    )
    def it_can_generate_random_tiles(
        self,
        request,
        tmpdir,
        coords1,
        coords2,
        check_tissue,
        has_enough_tissue,
        max_iter,
        expected_n_tiles,
    ):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _extract_tile = method_mock(request, Slide, "extract_tile")
        _has_enough_tissue = method_mock(request, Tile, "has_enough_tissue")
        _has_enough_tissue.side_effect = has_enough_tissue * (max_iter // 2)
        _random_tile_coordinates = method_mock(
            request, RandomTiler, "_random_tile_coordinates"
        )
        _random_tile_coordinates.side_effect = [coords1, coords2] * (max_iter // 2)
        tile1 = Tile(image, coords1)
        tile2 = Tile(image, coords2)
        _extract_tile.side_effect = [tile1, tile2] * (max_iter // 2)
        random_tiler = RandomTiler(
            (10, 10), 2, level=0, max_iter=max_iter, check_tissue=check_tissue
        )

        generated_tiles = list(random_tiler._random_tiles_generator(slide))

        _random_tile_coordinates.assert_called_with(random_tiler, slide)
        assert _random_tile_coordinates.call_count <= random_tiler.max_iter

        _extract_tile.call_args_list == ([call(coords1, 0), call(coords2, 0)])
        assert len(generated_tiles) == expected_n_tiles
        if expected_n_tiles == 2:
            assert generated_tiles == [(tile1, coords1), (tile2, coords2)]

    def it_can_extract_random_tiles(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, os.path.join(tmp_path_, "processed"))
        _random_tiles_generator = method_mock(
            request, RandomTiler, "_random_tiles_generator"
        )
        coords = CoordinatePair(0, 10, 0, 10)
        tile = Tile(image, coords)
        _random_tiles_generator.return_value = [(tile, coords), (tile, coords)]
        _tile_filename = method_mock(request, RandomTiler, "_tile_filename")
        _tile_filename.side_effect = [
            os.path.join(
                tmp_path_, "processed", "tiles", f"tile_{i}_level2_0-10-0-10.png"
            )
            for i in range(2)
        ]
        random_tiler = RandomTiler((10, 10), n_tiles=2, level=2)

        random_tiler.extract(slide)

        assert _tile_filename.call_args_list == [
            call(random_tiler, coords, 0),
            call(random_tiler, coords, 1),
        ]
        assert os.path.exists(
            os.path.join(tmp_path_, "processed", "tiles", "tile_0_level2_0-10-0-10.png")
        )
        assert os.path.exists(
            os.path.join(tmp_path_, "processed", "tiles", "tile_1_level2_0-10-0-10.png")
        )

    # fixtures -------------------------------------------------------

    @pytest.fixture(
        params=(
            (
                (512, 512),
                10,
                3,
                7,
                True,
                "",
                ".png",
                CoordinatePair(0, 512, 0, 512),
                3,
                "tile_3_level3_0-512-0-512.png",
            ),
            (
                (512, 512),
                10,
                0,
                7,
                True,
                "folder/",
                ".png",
                CoordinatePair(4, 127, 4, 127),
                10,
                "folder/tile_10_level0_4-127-4-127.png",
            ),
        )
    )
    def tile_filename_fixture(self, request):
        (
            tile_size,
            n_tiles,
            level,
            seed,
            check_tissue,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        ) = request.param
        return (
            tile_size,
            n_tiles,
            level,
            seed,
            check_tissue,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        )


class Describe_GridTiler(object):
    def it_constructs_from_args(self, request):
        _init = initializer_mock(request, GridTiler)

        grid_tiler = GridTiler((512, 512), 2, True, 0, "", ".png",)

        _init.assert_called_once_with(ANY, (512, 512), 2, True, 0, "", ".png")
        assert isinstance(grid_tiler, GridTiler)
        assert isinstance(grid_tiler, Tiler)

    def but_it_has_wrong_tile_size_value(self, request):
        with pytest.raises(ValueError) as err:
            GridTiler((512, -1))

        assert isinstance(err.value, ValueError)
        assert str(err.value) == "Tile size must be greater than 0 ((512, -1))"

    def or_it_has_not_available_level_value(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_50X50_RGB_RANDOM_COLOR
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        grid_tiler = GridTiler((512, 512), 3)

        with pytest.raises(LevelError) as err:
            grid_tiler.extract(slide)

        assert isinstance(err.value, LevelError)
        assert str(err.value) == "Level 3 not available. Number of available levels: 1"

    def or_it_has_negative_level_value(self, request):
        with pytest.raises(LevelError) as err:
            GridTiler((512, 512), -1)

        assert isinstance(err.value, LevelError)
        assert str(err.value) == "Level cannot be negative (-1)"

    @pytest.mark.parametrize("tile_size", ((512, 512), (128, 128), (10, 10)))
    def it_knows_its_tile_size(self, request, tile_size):
        grid_tiler = GridTiler(tile_size, 10, 0)

        tile_size_ = grid_tiler.tile_size

        assert type(tile_size_) == tuple
        assert tile_size_ == tile_size

    def it_knows_its_tile_filename(self, request, tile_filename_fixture):
        (
            tile_size,
            level,
            check_tissue,
            pixel_overlap,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        ) = tile_filename_fixture
        grid_tiler = GridTiler(
            tile_size, level, check_tissue, pixel_overlap, prefix, suffix
        )

        _filename = grid_tiler._tile_filename(tile_coords, tiles_counter)

        assert type(_filename) == str
        assert _filename == expected_filename

    @pytest.mark.parametrize(
        "check_tissue, expected_box",
        (
            (False, NpArrayMock.ONES_500X500_BOOL),
            (True, NpArrayMock.RANDOM_500X500_BOOL),
        ),
    )
    def it_knows_its_box_mask(self, request, tmpdir, check_tissue, expected_box):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _biggest_tissue_box_mask = property_mock(
            request, Slide, "biggest_tissue_box_mask"
        )
        _biggest_tissue_box_mask.return_value = expected_box
        grid_tiler = GridTiler((128, 128), 0, check_tissue=check_tissue)

        box_mask = grid_tiler.box_mask_thumb(slide)

        _biggest_tissue_box_mask.assert_called_once_with()
        assert type(box_mask) == np.ndarray
        np.testing.assert_array_almost_equal(box_mask, expected_box)

    @pytest.mark.parametrize(
        "bbox_coordinates, pixel_overlap, expected_n_tiles_row",
        (
            (CoordinatePair(x_ul=0, y_ul=0, x_br=6060, y_br=1917), 0, 11),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=1921, y_br=2187), 0, 3),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=1921, y_br=2187), 128, 5),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=1921, y_br=2187), -128, 3),
        ),
    )
    def it_can_calculate_n_tiles_row(
        self, request, bbox_coordinates, pixel_overlap, expected_n_tiles_row
    ):
        grid_tiler = GridTiler((512, 512), 2, True, pixel_overlap)

        n_tiles_row = grid_tiler._n_tiles_row(bbox_coordinates)

        assert type(n_tiles_row) == int
        assert n_tiles_row == expected_n_tiles_row

    @pytest.mark.parametrize(
        "bbox_coordinates, pixel_overlap, expected_n_tiles_column",
        (
            (CoordinatePair(x_ul=0, y_ul=0, x_br=6060, y_br=1917), 0, 3),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=6060, y_br=1917), -1, 3),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=1921, y_br=2187), 0, 4),
            (CoordinatePair(x_ul=0, y_ul=0, x_br=1921, y_br=2187), 128, 5),
        ),
    )
    def it_can_calculate_n_tiles_column(
        self, request, bbox_coordinates, pixel_overlap, expected_n_tiles_column
    ):
        grid_tiler = GridTiler((512, 512), 2, True, pixel_overlap)

        n_tiles_column = grid_tiler._n_tiles_column(bbox_coordinates)

        assert type(n_tiles_column) == int
        assert n_tiles_column == expected_n_tiles_column

    def it_can_generate_grid_tiles(
        self, request, tmpdir, grid_tiles_fixture,
    ):
        (
            coords1,
            coords2,
            check_tissue,
            has_enough_tissue,
            expected_n_tiles,
        ) = grid_tiles_fixture
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _extract_tile = method_mock(request, Slide, "extract_tile")
        _has_enough_tissue = method_mock(request, Tile, "has_enough_tissue")
        _has_enough_tissue.side_effect = has_enough_tissue
        _grid_coordinates_generator = method_mock(
            request, GridTiler, "_grid_coordinates_generator"
        )
        _grid_coordinates_generator.return_value = [coords1, coords2]
        tile1 = Tile(image, coords1)
        tile2 = Tile(image, coords2)
        _extract_tile.side_effect = [tile1, tile2]
        grid_tiler = GridTiler((10, 10), level=0, check_tissue=check_tissue)

        generated_tiles = list(grid_tiler._grid_tiles_generator(slide))

        _grid_coordinates_generator.assert_called_once_with(grid_tiler, slide)
        assert _extract_tile.call_args_list == (
            [call(slide, coords1, 0), call(slide, coords2, 0)]
        )
        assert len(generated_tiles) == expected_n_tiles
        if expected_n_tiles == 2:
            assert generated_tiles == [(tile1, coords1), (tile2, coords2)]
        if expected_n_tiles == 1:
            assert generated_tiles == [(tile1, coords1)]
        if expected_n_tiles == 0:
            assert generated_tiles == []

    def but_with_wrong_coordinates(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        _has_enough_tissue = method_mock(request, Tile, "has_enough_tissue")
        _has_enough_tissue.return_value = False
        _grid_coordinates_generator = method_mock(
            request, GridTiler, "_grid_coordinates_generator"
        )
        coords1 = CoordinatePair(600, 610, 600, 610)
        coords2 = CoordinatePair(0, 10, 0, 10)
        _grid_coordinates_generator.return_value = [coords1, coords2]
        grid_tiler = GridTiler((10, 10), level=0, check_tissue=False)

        generated_tiles = list(grid_tiler._grid_tiles_generator(slide))

        _grid_coordinates_generator.assert_called_once_with(grid_tiler, slide)
        assert len(generated_tiles) == 1
        # generated_tiles[0][0] is a Tile object but we don't know what object it is
        # because Slide.extract_tile is not mocked (for the exception to happen inside)
        assert isinstance(generated_tiles[0][0], Tile)
        assert generated_tiles[0][1] == coords2

    def and_doesnt_raise_error_with_wrong_coordinates(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, "processed")
        coords = CoordinatePair(5800, 6000, 5800, 6000)
        _grid_coordinates_generator = method_mock(
            request, GridTiler, "_grid_coordinates_generator"
        )
        _grid_coordinates_generator.return_value = [coords]
        grid_tiler = GridTiler((10, 10))
        generated_tiles = list(grid_tiler._grid_tiles_generator(slide))

        assert len(generated_tiles) == 0
        _grid_coordinates_generator.assert_called_once_with(grid_tiler, slide)

    def it_can_extract_grid_tiles(self, request, tmpdir):
        tmp_path_ = tmpdir.mkdir("myslide")
        image = PILImageMock.DIMS_500X500_RGBA_COLOR_155_249_240
        image.save(os.path.join(tmp_path_, "mywsi.png"), "PNG")
        slide_path = os.path.join(tmp_path_, "mywsi.png")
        slide = Slide(slide_path, os.path.join(tmp_path_, "processed"))
        _grid_tiles_generator = method_mock(request, GridTiler, "_grid_tiles_generator")
        coords = CoordinatePair(0, 10, 0, 10)
        tile = Tile(image, coords)
        _grid_tiles_generator.return_value = [(tile, coords), (tile, coords)]
        _tile_filename = method_mock(request, GridTiler, "_tile_filename")
        _tile_filename.side_effect = [
            os.path.join(
                tmp_path_, "processed", "tiles", f"tile_{i}_level2_0-10-0-10.png"
            )
            for i in range(2)
        ]
        grid_tiler = GridTiler((10, 10), level=0)

        grid_tiler.extract(slide)

        assert _tile_filename.call_args_list == [
            call(grid_tiler, coords, 0),
            call(grid_tiler, coords, 1),
        ]
        assert os.path.exists(
            os.path.join(tmp_path_, "processed", "tiles", "tile_0_level2_0-10-0-10.png")
        )
        assert os.path.exists(
            os.path.join(tmp_path_, "processed", "tiles", "tile_1_level2_0-10-0-10.png")
        )

    # fixtures -------------------------------------------------------

    @pytest.fixture(
        params=(
            (
                (512, 512),
                3,
                True,
                0,
                "",
                ".png",
                CoordinatePair(0, 512, 0, 512),
                3,
                "tile_3_level3_0-512-0-512.png",
            ),
            (
                (512, 512),
                0,
                True,
                0,
                "folder/",
                ".png",
                CoordinatePair(4, 127, 4, 127),
                10,
                "folder/tile_10_level0_4-127-4-127.png",
            ),
        )
    )
    def tile_filename_fixture(self, request):
        (
            tile_size,
            level,
            check_tissue,
            pixel_overlap,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        ) = request.param
        return (
            tile_size,
            level,
            check_tissue,
            pixel_overlap,
            prefix,
            suffix,
            tile_coords,
            tiles_counter,
            expected_filename,
        )

    @pytest.fixture(
        params=(
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [True, True],
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                False,
                [True, True],
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                False,
                [False, False],
                2,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [False, False],
                0,
            ),
            (
                CoordinatePair(0, 10, 0, 10),
                CoordinatePair(0, 10, 0, 10),
                True,
                [True, False],
                1,
            ),
        )
    )
    def grid_tiles_fixture(self, request):
        (
            coords1,
            coords2,
            check_tissue,
            has_enough_tissue,
            expected_n_tiles,
        ) = request.param
        return (
            coords1,
            coords2,
            check_tissue,
            has_enough_tissue,
            expected_n_tiles,
        )
