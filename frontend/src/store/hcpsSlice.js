import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { fetchHCPs } from "../api/api";

export const loadHCPs = createAsyncThunk("hcps/load", async () => {
  const res = await fetchHCPs();
  return res.data;
});

const hcpsSlice = createSlice({
  name: "hcps",
  initialState: { list: [], selectedHcpId: null, status: "idle" },
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadHCPs.pending, (state) => {
        state.status = "loading";
      })
      .addCase(loadHCPs.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.list = action.payload;
        if (!state.selectedHcpId && action.payload.length > 0) {
          state.selectedHcpId = action.payload[0].id;
        }
      })
      .addCase(loadHCPs.rejected, (state) => {
        state.status = "failed";
      });
  },
});

export const { selectHcp } = hcpsSlice.actions;
export default hcpsSlice.reducer;
