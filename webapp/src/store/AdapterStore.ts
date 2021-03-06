import {action, observable} from "mobx";
import axios from "axios";
import {ErrorStore} from "./ErrorStore";

// FIXME: adapter comes from JSON, not db?
// pipeline serialization should agree with above json
// integrate front end and back end :/
export type AdapterType = {
  id: string,
  description: string,
  inputs: { [key: string]: AdapterInputType; },
  outputs: { [key: string]: AdapterInputType; },
  func_type: string,
  friendly_name: string | null,
  example: { [key: string]: string; },
  is_fake?: boolean
};

export type AdapterInputType = {
  id: string,
  optional: boolean,
  val: string | null,
}

// FIXME: should pass in backend url via env var
export const flaskUrl = "/api"

export class AdapterStore {
  constructor(errorStore: ErrorStore) {
    this.errorStore = errorStore;
  }

  errorStore: ErrorStore
  @observable adapters: AdapterType[] = [];

  @action.bound getAdapters = () => {
    axios.get(`${flaskUrl}/adapters`).then(
      (resp) => {
        if ("data" in resp) {
          this.adapters = resp.data;
        } else {
          console.log("THERE IS SOMETHING WRONG!");
        }
      }
    );
  }
}