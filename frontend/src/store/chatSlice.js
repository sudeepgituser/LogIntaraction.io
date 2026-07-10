import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage } from "../api/api";
import { interactionAddedFromChat } from "./interactionsSlice";
import { selectHcp } from "./hcpsSlice";

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async (payload, { dispatch }) => {
    const res = await sendChatMessage(payload);
    if (res.data.interaction) {
      dispatch(interactionAddedFromChat(res.data.interaction));
      if (res.data.interaction.hcp_id) {
        dispatch(selectHcp(res.data.interaction.hcp_id));
      }
    }
    return res.data;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    sessionId: `session-${Date.now()}`,
    messages: [],
    status: "idle",
  },
  reducers: {
    userMessageAdded(state, action) {
      state.messages.push({ role: "user", content: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = "sending";
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "idle";
        state.messages.push({
          role: "assistant",
          content: action.payload.reply,
          toolCalls: action.payload.tool_calls,
        });
      })
      .addCase(sendMessage.rejected, (state) => {
        state.status = "idle";
        state.messages.push({
          role: "assistant",
          content: "Sorry, something went wrong reaching the agent.",
        });
      });
  },
});

export const { userMessageAdded } = chatSlice.actions;
export default chatSlice.reducer;
