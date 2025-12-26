import { useSprite, SpriteStyle } from '../context/SpriteContext'

const SPRITE_STYLES: SpriteStyle[] = ['default', 'official-artwork', 'home']

export default function SpriteStyleToggle() {
  const { spriteStyle, setSpriteStyle, getSpriteStyleLabel } = useSprite()

  return (
    <div className="sprite-style-toggle">
      <label htmlFor="sprite-style">Sprite Style:</label>
      <select
        id="sprite-style"
        value={spriteStyle}
        onChange={(e) => setSpriteStyle(e.target.value as SpriteStyle)}
      >
        {SPRITE_STYLES.map((style) => (
          <option key={style} value={style}>
            {getSpriteStyleLabel(style)}
          </option>
        ))}
      </select>
    </div>
  )
}
