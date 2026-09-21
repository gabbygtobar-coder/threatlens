/** Repo fixtures copied to web/public/samples. Real TLAL, not fabricated SOC events. */

export type SampleFixture = {
  id: string;
  label: string;
  path: string;
  expect: string;
};

export const SAMPLE_FIXTURES: SampleFixture[] = [
  {
    id: "normal",
    label: "normal",
    path: "/samples/normal.log",
    expect: "0 incidents",
  },
  {
    id: "bruteforce",
    label: "brute_force",
    path: "/samples/bruteforce.log",
    expect: "brute_force",
  },
  {
    id: "spray",
    label: "credential_spray",
    path: "/samples/spray.log",
    expect: "credential_spray",
  },
  {
    id: "unusual_login",
    label: "unusual_login",
    path: "/samples/unusual_login.log",
    expect: "unusual_login",
  },
  {
    id: "impossible_travel",
    label: "impossible_travel",
    path: "/samples/impossible_travel.log",
    expect: "impossible_travel (simulated geo)",
  },
  {
    id: "request_frequency",
    label: "request_frequency",
    path: "/samples/request_frequency.log",
    expect: "request_frequency",
  },
  {
    id: "restricted_access",
    label: "restricted_access",
    path: "/samples/restricted_access.log",
    expect: "restricted_access",
  },
  {
    id: "edge",
    label: "edge (parse errors)",
    path: "/samples/edge.log",
    expect: "parse errors + a few events",
  },
];
