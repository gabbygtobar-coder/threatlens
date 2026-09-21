export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          display_name: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          display_name?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          display_name?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
      analyses: {
        Row: {
          id: string;
          user_id: string;
          created_at: string;
          title: string | null;
          raw_log_text: string;
          events_count: number;
          parse_errors_count: number;
        };
        Insert: {
          id?: string;
          user_id: string;
          created_at?: string;
          title?: string | null;
          raw_log_text?: string;
          events_count?: number;
          parse_errors_count?: number;
        };
        Update: {
          id?: string;
          user_id?: string;
          created_at?: string;
          title?: string | null;
          raw_log_text?: string;
          events_count?: number;
          parse_errors_count?: number;
        };
        Relationships: [
          {
            foreignKeyName: "incidents_analysis_id_fkey";
            columns: ["id"];
            isOneToOne: false;
            referencedRelation: "incidents";
            referencedColumns: ["analysis_id"];
          },
        ];
      };
      incidents: {
        Row: {
          id: string;
          analysis_id: string;
          user_id: string;
          engine_incident_id: string | null;
          rule_id: string;
          severity: string;
          status: string;
          title: string;
          description: string;
          evidence: Json;
          created_at: string;
        };
        Insert: {
          id?: string;
          analysis_id: string;
          user_id: string;
          engine_incident_id?: string | null;
          rule_id: string;
          severity: string;
          status?: string;
          title: string;
          description?: string;
          evidence?: Json;
          created_at?: string;
        };
        Update: {
          id?: string;
          analysis_id?: string;
          user_id?: string;
          engine_incident_id?: string | null;
          rule_id?: string;
          severity?: string;
          status?: string;
          title?: string;
          description?: string;
          evidence?: Json;
          created_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "incidents_analysis_id_fkey";
            columns: ["analysis_id"];
            isOneToOne: false;
            referencedRelation: "analyses";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

export type AnalysisRow = Database["public"]["Tables"]["analyses"]["Row"];
export type IncidentRow = Database["public"]["Tables"]["incidents"]["Row"];
