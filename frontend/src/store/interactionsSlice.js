import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { fetchInteractions, createInteraction, updateInteraction } from "../api/api";

export const loadInteractions = createAsyncThunk(
  "interactions/load",
  async (hcpId) => {
    const res = await fetchInteractions(hcpId);
    return res.data;
  }
);

export const submitInteraction = createAsyncThunk(
  "interactions/submit",
  async (payload) => {
    const res = await createInteraction(payload);
    return res.data;
  }
);

export const editInteraction = createAsyncThunk(
  "interactions/edit",
  async ({ id, payload }) => {
    const res = await updateInteraction(id, payload);
    return res.data;
  }
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: { list: [], status: "idle", lastSubmitted: null, error: null },
  reducers: {
    interactionAddedFromChat(state, action) {
      state.list = state.list.filter((i) => i.id !== action.payload.id);
      state.list.unshift(action.payload);
      state.lastSubmitted = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadInteractions.fulfilled, (state, action) => {
        state.list = action.payload;
        state.status = "succeeded";
      })
      .addCase(submitInteraction.pending, (state) => {
        state.status = "submitting";
        state.error = null;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.list = state.list.filter((i) => i.id !== action.payload.id);
        state.list.unshift(action.payload);
        state.lastSubmitted = action.payload;
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(editInteraction.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.list[idx] = action.payload;
      });
  },
});

export const { interactionAddedFromChat } = interactionsSlice.actions;
export default interactionsSlice.reducer;