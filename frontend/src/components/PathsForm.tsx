import { PATH_FIELDS, type DataPaths } from "../lib/paths";
import { page } from "../lib/theme";

type Props = {
  paths: DataPaths;
  setPaths: React.Dispatch<React.SetStateAction<DataPaths>>;
};

export function PathsForm({ paths, setPaths }: Props) {
  return (
    <div className="space-y-4">
      {PATH_FIELDS.map(({ key, label, placeholder }) => (
        <label key={key} className="block">
          <span className={page.label}>{label}</span>
          <input
            className="ui-input mt-2 font-mono text-xs"
            value={paths[key]}
            onChange={(e) => setPaths((p) => ({ ...p, [key]: e.target.value }))}
            placeholder={placeholder}
          />
        </label>
      ))}
    </div>
  );
}
