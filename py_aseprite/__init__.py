from .headers import Header, Frame
from .chunks import (
    Chunk,
    OldPaleteChunk_0x0004,
    OldPaleteChunk_0x0011,
    LayerChunk,
    LayerGroupChunk,
    CelChunk,
    CelExtraChunk,
    MaskChunk,
    FrameTagsChunk,
    PathChunk,
    PaletteChunk,
    UserDataChunk,
    SliceChunk
)


class AsepriteFile(object):
    def __init__(self, data):
        self.header, self.frames = AsepriteFile.parse_data(data)
        self.build_layer_tree()

    def build_layer_tree(self):
        # Assuming that layers are stored in chunk #0.
        # Warn me if they're stored in another chunk
        self.layers = [chunk for chunk in self.frames[0].chunks if isinstance(chunk, LayerChunk)]
        stack = []
        self.layer_tree = []
        for layer in self.layers:
            while layer.layer_child_level < len(stack):
                stack.pop()

            if len(stack) > 0:
                stack[len(stack) - 1].children.append(layer)
            else:
                self.layer_tree.append(layer)

            if isinstance(layer, LayerGroupChunk):
                stack.append(layer)


    @staticmethod
    def parse_data(data):
        head = Header(data)
        data_offset = Header.header_size
        frames = []
        layer_index = 0
        supported_chunks = (
            OldPaleteChunk_0x0004,
            OldPaleteChunk_0x0011,
            LayerChunk,
            CelChunk,
            CelExtraChunk,
            MaskChunk,
            FrameTagsChunk,
            PathChunk,
            PaletteChunk,
            UserDataChunk,
            SliceChunk
        )
        for i in range(head.num_frames):
            frame = Frame(data, data_offset)
            frames.append(frame)
            frame.chunks = []
            data_offset += frame.frame_size
            for c in range(frame.num_chunks):
                chunk = Chunk(data, data_offset)
                found_chunk_type = None
                for chunk_type in supported_chunks:
                    if chunk_type.chunk_id == chunk.chunk_type:
                        found_chunk_type = chunk_type
                        break

                if not found_chunk_type:
                    print("Skipped 0x{:04x}".format(chunk.chunk_type))

                elif found_chunk_type == LayerChunk:
                    layer = LayerChunk(data, layer_index, data_offset)
                    if layer.layer_type & 1 == 1:
                        frame.chunks.append(LayerGroupChunk(layer))
                    else:
                        frame.chunks.append(layer)

                        layer_index += 1
                else:
                    frame.chunks.append(found_chunk_type(data, data_offset))

                data_offset += chunk.chunk_size

        return head, frames
