import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LocationInput } from '../../components/Controls/LocationInput'

describe('LocationInput', () => {
  it('renders lat and lon inputs and load button', () => {
    const onLoad = vi.fn()
    render(<LocationInput onLoad={onLoad} />)
    expect(screen.getByTestId('lat-input')).toBeInTheDocument()
    expect(screen.getByTestId('lon-input')).toBeInTheDocument()
    expect(screen.getByTestId('load-map')).toBeInTheDocument()
  })

  it('calls onLoad with parsed coordinates when Load Map is clicked', () => {
    const onLoad = vi.fn()
    render(<LocationInput onLoad={onLoad} />)
    fireEvent.change(screen.getByTestId('lat-input'), { target: { value: '35.1234' } })
    fireEvent.change(screen.getByTestId('lon-input'), { target: { value: '-80.5678' } })
    fireEvent.click(screen.getByTestId('load-map'))
    expect(onLoad).toHaveBeenCalledWith(35.1234, -80.5678)
  })
})
